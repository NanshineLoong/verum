"""
简单的 Query Engine API 服务器
提供 POST 接口接收查询并返回报告
"""

import os
import sys
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from loguru import logger
from typing import Dict, Any, Optional

# 设置UTF-8编码环境
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from QueryEngine import DeepSearchAgent, Settings
from config import settings as global_settings

# 导入浅度思考模式（快速思考）
deepsearch_demo_path = os.path.join(os.path.dirname(__file__), 'DeepSearchAgent-Demo')
sys.path.insert(0, deepsearch_demo_path)
from src import DeepSearchAgent as QuickSearchAgent

# 导入判罚服务和时间线服务（从backend目录）
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
from verification_service import VerificationService, create_verification_service
from timeline_service import TimelineService, create_timeline_service

app = Flask(__name__, static_folder='static')
CORS(app)  # 允许跨域请求

# 全局变量：存储不同类型的任务
tasks: Dict[str, 'QueryTask'] = {}
verification_tasks: Dict[str, 'VerificationTask'] = {}
timeline_tasks: Dict[str, 'TimelineTask'] = {}
task_lock = threading.Lock()
verification_lock = threading.Lock()
timeline_lock = threading.Lock()


class QueryTask:
    """查询任务类"""
    
    def __init__(self, query: str, task_id: str, mode: str = "deep"):
        self.task_id = task_id
        self.query = query
        self.mode = mode  # "deep" 深度思考 或 "quick" 浅度思考
        self.status = "pending"  # pending, running, completed, error
        self.progress = 0
        self.report = None
        self.verification_result = None  # 判罚结果
        self.state_data = None  # 保存状态数据，用于生成时间线
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
            'mode': self.mode,
            'status': self.status,
            'progress': self.progress,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'has_result': bool(self.report),
            'has_verification': bool(self.verification_result),
            'has_timeline': bool(self.state_data)
        }


class VerificationTask:
    """判罚任务类"""
    
    def __init__(self, query: str, report: str, verification_id: str):
        self.verification_id = verification_id
        self.query = query
        self.report = report
        self.status = "pending"  # pending, running, completed, error
        self.progress = 0
        self.result = None
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
            'verification_id': self.verification_id,
            'query': self.query[:100] + '...' if len(self.query) > 100 else self.query,
            'status': self.status,
            'progress': self.progress,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'has_result': bool(self.result)
        }


class TimelineTask:
    """时间线任务类"""
    
    def __init__(self, state_data: Dict[str, Any], timeline_id: str):
        self.timeline_id = timeline_id
        self.state_data = state_data
        self.status = "pending"  # pending, running, completed, error
        self.progress = 0
        self.result = None
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
            'timeline_id': self.timeline_id,
            'status': self.status,
            'progress': self.progress,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'has_result': bool(self.result)
        }


@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory('static', 'query_frontend.html')


def run_query_task(task: QueryTask, query_text: str):
    """在后台线程中运行查询任务"""
    try:
        task.update_status("running", 10)
        
        # 检查必要的配置
        if not global_settings.TAVILY_API_KEY:
            task.update_status("error", 0, '请在环境变量中设置 TAVILY_API_KEY')
            return
        
        report = None
        
        if task.mode == "deep":
            # 深度思考模式 - 使用 QueryEngine
            if not global_settings.QUERY_ENGINE_API_KEY:
                task.update_status("error", 0, '请在环境变量中设置 QUERY_ENGINE_API_KEY')
                return
            
            logger.info("使用深度思考模式（QueryEngine）")
            task.update_status("running", 20)
            
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
            logger.info("正在初始化深度思考 Agent...")
            agent = DeepSearchAgent(config)
            
            logger.info("正在生成报告...")
            task.update_status("running", 30)
            report = agent.research(query_text, save_report=True)
            
            # 保存状态数据用于生成时间线
            try:
                task.state_data = agent.state.to_dict()
                logger.info(f"深度模式：状态数据已保存，paragraphs数量: {len(task.state_data.get('paragraphs', []))}")
            except Exception as e:
                logger.error(f"保存状态数据失败: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
            
        else:
            # 浅度思考模式 - 使用 DeepSearchAgent-Demo
            if not global_settings.QUERY_ENGINE_API_KEY:
                task.update_status("error", 0, '请在环境变量中设置 QUERY_ENGINE_API_KEY（浅度模式也需要LLM）')
                return
            
            logger.info("使用浅度思考模式（DeepSearchAgent-Demo）")
            task.update_status("running", 20)
            
            # 直接从 global_settings 创建配置对象
            from src.utils.config import Config
            quick_config = Config(
                deepseek_api_key=global_settings.QUERY_ENGINE_API_KEY,
                openai_api_key=None,  # 浅度模式使用 deepseek
                tavily_api_key=global_settings.TAVILY_API_KEY,
                default_llm_provider="deepseek",
                deepseek_model=global_settings.QUERY_ENGINE_MODEL_NAME or "deepseek-chat",
                openai_model="gpt-4o-mini",
                max_search_results=3,
                search_timeout=240,
                max_content_length=20000,
                max_reflections=2,
                max_paragraphs=5,
                output_dir="query_engine_streamlit_reports",
                save_intermediate_states=True
            )
            
            # 验证配置
            if not quick_config.validate():
                task.update_status("error", 0, '浅度模式配置验证失败，请检查环境变量中的API密钥')
                return
            
            # 创建 Agent 并执行研究
            logger.info("正在初始化浅度思考 Agent...")
            agent = QuickSearchAgent(quick_config)
            
            logger.info("正在生成报告...")
            task.update_status("running", 30)
            report = agent.research(query_text, save_report=True)
            
            # 保存状态数据用于生成时间线
            try:
                task.state_data = agent.state.to_dict()
                logger.info(f"浅度模式：状态数据已保存，paragraphs数量: {len(task.state_data.get('paragraphs', []))}")
            except Exception as e:
                logger.error(f"保存状态数据失败: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
        # 保存报告结果
        task.report = report
        task.update_status("running", 80)
        
        # 执行判罚
        logger.info("正在进行新闻真假判别...")
        try:
            # 创建判罚服务
            verification_service = create_verification_service(
                api_key=global_settings.QUERY_ENGINE_API_KEY,
                provider="deepseek",
                model_name=global_settings.QUERY_ENGINE_MODEL_NAME or "deepseek-chat",
                output_dir="query_engine_streamlit_reports"
            )
            
            # 执行判罚
            verification_result = verification_service.verify_news(
                query=query_text,
                final_report=report,
                save_result=True,
                output_dir="query_engine_streamlit_reports"
            )
            
            task.verification_result = verification_result
            logger.info(f"判罚完成: {verification_result.get('verdict', '未知')}")
            
        except Exception as e:
            logger.error(f"判罚过程出错: {str(e)}")
            # 判罚失败不影响主流程
            task.verification_result = {
                "verdict": "无法确定",
                "summary": f"判罚过程出错: {str(e)}",
                "error": str(e)
            }
        
        task.update_status("completed", 100)
        logger.info("任务完成")
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"查询任务执行失败: {str(e)}\n{error_traceback}")
        task.update_status("error", 0, str(e))


def run_verification_task(task: VerificationTask):
    """在后台线程中运行判罚任务"""
    try:
        task.update_status("running", 10)
        
        # 检查必要的配置
        if not global_settings.QUERY_ENGINE_API_KEY:
            task.update_status("error", 0, '请在环境变量中设置 QUERY_ENGINE_API_KEY')
            return
        
        logger.info("开始执行判罚任务...")
        task.update_status("running", 30)
        
        # 创建判罚服务
        verification_service = create_verification_service(
            api_key=global_settings.QUERY_ENGINE_API_KEY,
            provider="deepseek",
            model_name=global_settings.QUERY_ENGINE_MODEL_NAME or "deepseek-chat",
            output_dir="query_engine_streamlit_reports"
        )
        
        task.update_status("running", 50)
        
        # 执行判罚
        verification_result = verification_service.verify_news(
            query=task.query,
            final_report=task.report,
            save_result=True,
            output_dir="query_engine_streamlit_reports"
        )
        
        # 保存结果
        task.result = verification_result
        task.update_status("completed", 100)
        logger.info(f"判罚任务完成: {verification_result.get('verdict', '未知')}")
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"判罚任务执行失败: {str(e)}\n{error_traceback}")
        task.update_status("error", 0, str(e))


def run_timeline_task(task: TimelineTask):
    """在后台线程中运行时间线任务"""
    try:
        task.update_status("running", 10)
        
        logger.info("开始生成时间线...")
        task.update_status("running", 30)
        
        # 创建时间线服务
        timeline_service = create_timeline_service()
        
        task.update_status("running", 50)
        
        # 生成时间线
        timeline_result = timeline_service.generate_timeline(task.state_data)
        
        if timeline_result.get("error"):
            task.update_status("error", 0, timeline_result.get("error"))
            return
        
        # 保存结果
        task.result = timeline_result
        task.update_status("completed", 100)
        logger.info("时间线生成完成")
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"时间线任务执行失败: {str(e)}\n{error_traceback}")
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
        
        # 获取思考模式，默认为深度思考
        mode = data.get('mode', 'deep').lower()
        if mode not in ['deep', 'quick']:
            mode = 'deep'
        
        logger.info(f"收到查询请求: {query_text}, 模式: {mode}")
        
        # 创建新任务
        task_id = f"query_{int(time.time())}"
        task = QueryTask(query_text, task_id, mode=mode)
        
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
            'report': task.report,
            'verification': task.verification_result
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


@app.route('/api/verification', methods=['POST'])
def create_verification():
    """
    创建独立的新闻真假判别任务
    
    请求格式:
    {
        "query": "原始查询/新闻内容",
        "report": "研究报告内容（可选，如果不提供则需要提供task_id）",
        "task_id": "任务ID（可选，如果不提供report则需要提供task_id）"
    }
    
    返回格式:
    {
        "success": true,
        "verification_id": "verification_1234567890",
        "message": "判罚任务已创建",
        "verification": {...}
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请提供请求数据'
            }), 400
        
        query = data.get('query', '').strip()
        report = data.get('report', '').strip()
        task_id = data.get('task_id', '').strip()
        
        # 如果没有提供report，尝试从task_id获取
        if not report and task_id:
            with task_lock:
                task = tasks.get(task_id)
            if task and task.report:
                report = task.report
                if not query:
                    query = task.query
            else:
                return jsonify({
                    'success': False,
                    'error': f'任务 {task_id} 不存在或没有报告内容'
                }), 404
        
        # 验证必需参数
        if not query:
            return jsonify({
                'success': False,
                'error': '请提供查询内容 (query 字段) 或任务ID (task_id 字段)'
            }), 400
        
        if not report:
            return jsonify({
                'success': False,
                'error': '请提供研究报告内容 (report 字段) 或任务ID (task_id 字段)'
            }), 400
        
        logger.info(f"收到判罚请求: query={query[:50]}..., report_length={len(report)}")
        
        # 创建新任务
        verification_id = f"verification_{int(time.time())}"
        verification_task = VerificationTask(query, report, verification_id)
        
        with verification_lock:
            verification_tasks[verification_id] = verification_task
        
        # 在后台线程中运行判罚
        thread = threading.Thread(
            target=run_verification_task,
            args=(verification_task,),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            'success': True,
            'verification_id': verification_id,
            'message': '判罚任务已创建',
            'verification': verification_task.to_dict()
        })
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"创建判罚任务失败: {str(e)}\n{error_traceback}")
        
        return jsonify({
            'success': False,
            'error': f'创建判罚任务失败: {str(e)}'
        }), 500


@app.route('/api/verification/<verification_id>', methods=['GET'])
def get_verification_result(verification_id: str):
    """
    获取判罚结果
    
    返回格式:
    {
        "success": true,
        "verification": {...},
        "result": {...}
    }
    """
    try:
        with verification_lock:
            verification_task = verification_tasks.get(verification_id)
        
        if not verification_task:
            return jsonify({
                'success': False,
                'error': '判罚任务不存在'
            }), 404
        
        if verification_task.status == "pending" or verification_task.status == "running":
            return jsonify({
                'success': False,
                'error': '判罚尚未完成',
                'verification': verification_task.to_dict()
            }), 400
        
        if verification_task.status == "error":
            return jsonify({
                'success': False,
                'error': verification_task.error_message,
                'verification': verification_task.to_dict()
            }), 500
        
        # 任务完成，返回结果
        return jsonify({
            'success': True,
            'verification': verification_task.to_dict(),
            'result': verification_task.result
        })
        
    except Exception as e:
        logger.exception(f"获取判罚结果失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/verification/<verification_id>/status', methods=['GET'])
def get_verification_status(verification_id: str):
    """
    获取判罚任务状态
    
    返回格式:
    {
        "success": true,
        "verification": {...}
    }
    """
    try:
        with verification_lock:
            verification_task = verification_tasks.get(verification_id)
        
        if not verification_task:
            return jsonify({
                'success': False,
                'error': '判罚任务不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'verification': verification_task.to_dict()
        })
        
    except Exception as e:
        logger.exception(f"获取判罚任务状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/timeline', methods=['POST'])
def create_timeline():
    """
    创建时间线任务
    
    请求格式:
    {
        "task_id": "任务ID"  // 可选，如果不提供则需要提供state_data
        "state_data": {...}  // 可选，状态数据
    }
    
    返回格式:
    {
        "success": true,
        "timeline_id": "timeline_1234567890",
        "message": "时间线任务已创建",
        "timeline": {...}
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请提供请求数据'
            }), 400
        
        task_id = data.get('task_id', '').strip()
        state_data = data.get('state_data')
        
        # 如果没有提供state_data，尝试从task_id获取
        if not state_data and task_id:
            with task_lock:
                task = tasks.get(task_id)
            if task and task.state_data:
                state_data = task.state_data
            else:
                return jsonify({
                    'success': False,
                    'error': f'任务 {task_id} 不存在或没有状态数据'
                }), 404
        
        if not state_data:
            return jsonify({
                'success': False,
                'error': '请提供状态数据 (state_data) 或任务ID (task_id)'
            }), 400
        
        logger.info(f"收到时间线生成请求: task_id={task_id}, has_state_data={bool(state_data)}")
        
        # 创建新任务
        timeline_id = f"timeline_{int(time.time())}"
        timeline_task = TimelineTask(state_data, timeline_id)
        
        with timeline_lock:
            timeline_tasks[timeline_id] = timeline_task
        
        # 在后台线程中运行时间线生成
        thread = threading.Thread(
            target=run_timeline_task,
            args=(timeline_task,),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            'success': True,
            'timeline_id': timeline_id,
            'message': '时间线任务已创建',
            'timeline': timeline_task.to_dict()
        })
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"创建时间线任务失败: {str(e)}\n{error_traceback}")
        
        return jsonify({
            'success': False,
            'error': f'创建时间线任务失败: {str(e)}'
        }), 500


@app.route('/api/timeline/<timeline_id>', methods=['GET'])
def get_timeline_result(timeline_id: str):
    """
    获取时间线结果
    
    返回格式:
    {
        "success": true,
        "timeline": {...},
        "result": {...}
    }
    """
    try:
        with timeline_lock:
            timeline_task = timeline_tasks.get(timeline_id)
        
        if not timeline_task:
            return jsonify({
                'success': False,
                'error': '时间线任务不存在'
            }), 404
        
        if timeline_task.status == "pending" or timeline_task.status == "running":
            return jsonify({
                'success': False,
                'error': '时间线生成尚未完成',
                'timeline': timeline_task.to_dict()
            }), 400
        
        if timeline_task.status == "error":
            return jsonify({
                'success': False,
                'error': timeline_task.error_message,
                'timeline': timeline_task.to_dict()
            }), 500
        
        # 任务完成，返回结果
        return jsonify({
            'success': True,
            'timeline': timeline_task.to_dict(),
            'result': timeline_task.result
        })
        
    except Exception as e:
        logger.exception(f"获取时间线结果失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/timeline/<timeline_id>/status', methods=['GET'])
def get_timeline_status(timeline_id: str):
    """
    获取时间线任务状态
    
    返回格式:
    {
        "success": true,
        "timeline": {...}
    }
    """
    try:
        with timeline_lock:
            timeline_task = timeline_tasks.get(timeline_id)
        
        if not timeline_task:
            return jsonify({
                'success': False,
                'error': '时间线任务不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'timeline': timeline_task.to_dict()
        })
        
    except Exception as e:
        logger.exception(f"获取时间线任务状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



if __name__ == '__main__':
    logger.info("启动 API 服务器...")
    app.run(host='0.0.0.0', port=6001, debug=True)

