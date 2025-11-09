"""
Query Engine API 服务器
提供 QueryEngine 的 REST API 接口

注意：此文件从 @bettafish 子模块导入 QueryEngine，不修改子模块内部文件
"""

import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from loguru import logger
from typing import Dict, Any

# 设置UTF-8编码环境
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# 添加项目根目录和 @bettafish 到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BETTAFISH_ROOT = PROJECT_ROOT / "@bettafish"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BETTAFISH_ROOT))

# 从 @bettafish 子模块导入
from QueryEngine import DeepSearchAgent, Settings
from config import settings as global_settings

app = Flask(__name__, static_folder='../static')
CORS(app)  # 允许跨域请求

# 全局变量：存储任务
tasks: Dict[str, 'QueryTask'] = {}
task_lock = threading.Lock()


class QueryTask:
    """查询任务类"""
    
    def __init__(self, query: str, task_id: str):
        self.task_id = task_id
        self.query = query
        self.status = "pending"  # pending, running, completed, error
        self.progress = 0
        self.report = None
        self.error_message = ""
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def update_status(self, status: str, progress: int = None, error_message: str = ""):
        """更新任务状态"""
        self.status = status
        if progress is not None:
            self.progress = progress
        if error_message:
            self.error_message = error_message
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'task_id': self.task_id,
            'query': self.query,
            'status': self.status,
            'progress': self.progress,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'has_result': bool(self.report)
        }


@app.route('/')
def index():
    """返回 API 信息"""
    return jsonify({
        'service': 'Query Engine API',
        'version': '1.0.0',
        'endpoints': {
            'health': 'GET /health',
            'create_query': 'POST /api/query',
            'get_result': 'GET /api/query/<task_id>',
            'get_status': 'GET /api/query/<task_id>/status'
        },
        'example_frontend': '/examples/query_frontend.html'
    })


def run_query_task(task: QueryTask, query_text: str):
    """在后台线程中运行查询任务"""
    try:
        task.update_status("running", 10)
        
        # 检查必要的配置
        if not global_settings.QUERY_ENGINE_API_KEY:
            task.update_status("error", 0, '请在环境变量中设置 QUERY_ENGINE_API_KEY')
            return
        
        if not global_settings.TAVILY_API_KEY:
            task.update_status("error", 0, '请在环境变量中设置 TAVILY_API_KEY')
            return
        
        # 创建配置
        config = Settings(
            QUERY_ENGINE_API_KEY=global_settings.QUERY_ENGINE_API_KEY,
            QUERY_ENGINE_BASE_URL=global_settings.QUERY_ENGINE_BASE_URL,
            QUERY_ENGINE_MODEL_NAME=global_settings.QUERY_ENGINE_MODEL_NAME or "deepseek-chat",
            TAVILY_API_KEY=global_settings.TAVILY_API_KEY,
            MAX_REFLECTIONS=2,
            SEARCH_CONTENT_MAX_LENGTH=20000,
            OUTPUT_DIR="query_engine_streamlit_reports"
        )
        
        # 创建 Agent 并执行研究
        logger.info("正在初始化 Agent...")
        task.update_status("running", 20)
        agent = DeepSearchAgent(config)
        
        logger.info("正在生成报告...")
        task.update_status("running", 30)
        report = agent.research(query_text, save_report=True)
        
        # 保存结果
        task.report = report
        task.update_status("completed", 100)
        logger.info("报告生成完成")
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"查询任务执行失败: {str(e)}\n{error_traceback}")
        task.update_status("error", 0, str(e))


@app.route('/api/query', methods=['POST'])
def create_query():
    """
    创建查询任务
    
    请求格式:
    {
        "query": "你的问题"
    }
    
    返回格式:
    {
        "success": true,
        "task_id": "query_1234567890",
        "message": "查询任务已创建",
        "task": {...}
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': '请提供查询内容 (query 字段)'
            }), 400
        
        query_text = data['query'].strip()
        if not query_text:
            return jsonify({
                'success': False,
                'error': '查询内容不能为空'
            }), 400
        
        logger.info(f"收到查询请求: {query_text}")
        
        # 创建新任务
        task_id = f"query_{int(time.time())}"
        task = QueryTask(query_text, task_id)
        
        with task_lock:
            tasks[task_id] = task
        
        # 在后台线程中运行查询
        thread = threading.Thread(
            target=run_query_task,
            args=(task, query_text),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '查询任务已创建',
            'task': task.to_dict()
        })
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"创建查询任务失败: {str(e)}\n{error_traceback}")
        
        return jsonify({
            'success': False,
            'error': f'创建查询任务失败: {str(e)}'
        }), 500


@app.route('/api/query/<task_id>', methods=['GET'])
def get_query_result(task_id: str):
    """
    获取查询结果
    
    返回格式:
    {
        "success": true,
        "task": {...},
        "report": "报告内容"
    }
    """
    try:
        with task_lock:
            task = tasks.get(task_id)
        
        if not task:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404
        
        if task.status == "pending" or task.status == "running":
            return jsonify({
                'success': False,
                'error': '查询尚未完成',
                'task': task.to_dict()
            }), 400
        
        if task.status == "error":
            return jsonify({
                'success': False,
                'error': task.error_message,
                'task': task.to_dict()
            }), 500
        
        # 任务完成，返回结果
        return jsonify({
            'success': True,
            'task': task.to_dict(),
            'report': task.report
        })
        
    except Exception as e:
        logger.exception(f"获取查询结果失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/query/<task_id>/status', methods=['GET'])
def get_query_status(task_id: str):
    """
    获取查询任务状态
    
    返回格式:
    {
        "success": true,
        "task": {...}
    }
    """
    try:
        with task_lock:
            task = tasks.get(task_id)
        
        if not task:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'task': task.to_dict()
        })
        
    except Exception as e:
        logger.exception(f"获取查询任务状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("启动 Query Engine API 服务器...")
    logger.info(f"项目根目录: {PROJECT_ROOT}")
    logger.info(f"@bettafish 路径: {BETTAFISH_ROOT}")
    app.run(host='0.0.0.0', port=6001, debug=True)

