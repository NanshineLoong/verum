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
from QueryEngine.llms.base import LLMClient
from config import settings as global_settings

# 导入浅度思考模式（快速思考）
deepsearch_demo_path = os.path.join(os.path.dirname(__file__), 'DeepSearchAgent-Demo')
sys.path.insert(0, deepsearch_demo_path)
from src import DeepSearchAgent as QuickSearchAgent

# 导入判罚服务
from verification_service import VerificationService, create_verification_service

# 导入时间线服务
from timeline_service import TimelineService, create_timeline_service

app = Flask(__name__, static_folder='static')
CORS(app)  # 允许跨域请求

# 全局变量：存储任务
tasks: Dict[str, 'QueryTask'] = {}
task_lock = threading.Lock()


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


@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory('static', 'query_frontend.html')


def determine_query_mode(query: str) -> str:
    """
    使用 LLM 判断查询应该使用深度思考还是浅度思考模式
    
    Args:
        query: 用户查询内容
        
    Returns:
        "deep" 或 "quick"
    """
    try:
        # 检查必要的配置
        if not global_settings.QUERY_ENGINE_API_KEY:
            logger.warning("QUERY_ENGINE_API_KEY 未设置，默认使用浅度思考模式")
            return "quick"
        
        # 创建 LLM 客户端
        llm_client = LLMClient(
            api_key=global_settings.QUERY_ENGINE_API_KEY,
            model_name=global_settings.QUERY_ENGINE_MODEL_NAME or "deepseek-chat",
            base_url=global_settings.QUERY_ENGINE_BASE_URL
        )
        
        # 构建系统提示词
        system_prompt = """你是一个智能查询分析助手。你的任务是根据用户的查询内容，判断应该使用哪种思考模式。

我们有两种思考模式：
1. **深度思考模式（deep）**：适合复杂、需要深入分析、多角度思考的查询
   - 需要综合分析多个信息源
   - 需要深入推理和逻辑分析
   - 涉及复杂的事件、趋势、因果关系分析
   - 需要多轮反思和验证
   - 例如："分析某事件的深层原因和影响"、"某政策的长期影响"、"复杂的社会现象分析"

2. **浅度思考模式（quick）**：适合简单、直接、事实性查询
   - 主要是信息检索和事实确认
   - 查询内容明确、直接
   - 不需要复杂的推理过程
   - 例如："某公司的最新股价"、"某个新闻事件的基本事实"、"简单的数据查询"

请根据查询内容的特点，只返回 "deep" 或 "quick"，不要返回其他内容。"""

        # 构建用户提示词
        user_prompt = f"""请分析以下查询，判断应该使用深度思考模式还是浅度思考模式：

查询内容：{query}

请只返回 "deep" 或 "quick"。"""
        
        # 调用 LLM
        logger.info("正在使用 LLM 判断查询模式...")
        response = llm_client.invoke(system_prompt, user_prompt, temperature=0.3)
        
        # 解析响应
        response = response.strip().lower()
        if "deep" in response:
            mode = "deep"
        elif "quick" in response:
            mode = "quick"
        else:
            # 如果无法判断，默认使用深度思考模式
            logger.warning(f"LLM 返回了无法识别的模式: {response}，默认使用深度思考模式")
            mode = "deep"
        
        logger.info(f"查询模式判断结果: {mode} (原始响应: {response})")
        return mode
        
    except Exception as e:
        logger.error(f"判断查询模式失败: {str(e)}，默认使用深度思考模式")
        import traceback
        logger.error(traceback.format_exc())
        return "quick"


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


@app.route('/api/query', methods=['POST'])
def create_query():
    """
    创建查询任务
    
    请求格式:
    {
        "query": "你的问题",
        "mode": "deep" | "quick" | "auto"  // 可选，默认为 "auto"（自动判断）
                                          // "auto" 表示使用 LLM 自动判断使用深度还是浅度思考
                                          // 只有明确指定 "deep" 或 "quick" 时才使用指定模式
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
        
        # 获取思考模式，默认为自动判断
        mode = data.get('mode', 'auto').lower()
        
        # 如果模式是 "auto"，使用 LLM 自动判断
        if mode == 'auto':
            logger.info(f"收到查询请求: {query_text}, 模式: auto (将自动判断)")
            mode = determine_query_mode(query_text)
            logger.info(f"自动判断结果: {mode}")
        elif mode not in ['deep', 'quick']:
            # 如果提供了无效的模式，默认使用自动判断
            logger.warning(f"无效的模式: {mode}，使用自动判断")
            mode = determine_query_mode(query_text)
        
        logger.info(f"收到查询请求: {query_text}, 最终模式: {mode}")
        
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
        
        logger.info(f"收到独立判罚请求: query={query[:50]}..., report_length={len(report)}")
        
        # 检查必要的配置
        if not global_settings.QUERY_ENGINE_API_KEY:
            return jsonify({
                'success': False,
                'error': '请在环境变量中设置 QUERY_ENGINE_API_KEY'
            }), 500
        
        # 创建判罚服务并立即执行
        try:
            verification_service = create_verification_service(
                api_key=global_settings.QUERY_ENGINE_API_KEY,
                provider="deepseek",
                model_name=global_settings.QUERY_ENGINE_MODEL_NAME or "deepseek-chat",
                output_dir="query_engine_streamlit_reports"
            )
            
            # 执行判罚
            verification_result = verification_service.verify_news(
                query=query,
                final_report=report,
                save_result=True,
                output_dir="query_engine_streamlit_reports"
            )
            
            logger.info(f"判罚完成: {verification_result.get('verdict', '未知')}")
            
            return jsonify({
                'success': True,
                'verification': verification_result,
                'message': '判罚完成'
            })
            
        except Exception as e:
            logger.error(f"判罚过程出错: {str(e)}")
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"错误堆栈: {error_traceback}")
            
            return jsonify({
                'success': False,
                'error': f'判罚过程出错: {str(e)}',
                'verification': {
                    "verdict": "无法确定",
                    "summary": f"判罚过程出错: {str(e)}",
                    "error": str(e)
                }
            }), 500
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"创建判罚任务失败: {str(e)}\n{error_traceback}")
        
        return jsonify({
            'success': False,
            'error': f'创建判罚任务失败: {str(e)}'
        }), 500


@app.route('/api/verification/query/<task_id>', methods=['GET'])
def get_verification_by_task(task_id: str):
    """
    根据任务ID获取判罚结果
    
    返回格式:
    {
        "success": true,
        "verification": {...}
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
        
        if not task.verification_result:
            return jsonify({
                'success': False,
                'error': '该任务还没有判罚结果'
            }), 404
        
        return jsonify({
            'success': True,
            'verification': task.verification_result,
            'task': task.to_dict()
        })
        
    except Exception as e:
        logger.exception(f"获取判罚结果失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/timeline/generate', methods=['POST'])
def generate_timeline():
    """
    生成时间线
    
    请求格式:
    {
        "task_id": "任务ID"  // 可选，如果不提供则需要提供state_data
        "state_data": {...}  // 可选，状态数据
    }
    
    返回格式:
    {
        "success": true,
        "timeline": [...],
        "total_sources": 15,
        "date_range": {"start": "2025.08.08", "end": "2025.10.09"}
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
        
        # 创建时间线服务并生成时间线
        timeline_service = create_timeline_service()
        timeline_result = timeline_service.generate_timeline(state_data)
        
        if timeline_result.get("error"):
            return jsonify({
                'success': False,
                'error': timeline_result.get("error"),
                'timeline': timeline_result
            }), 500
        
        return jsonify({
            'success': True,
            **timeline_result
        })
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"生成时间线失败: {str(e)}\n{error_traceback}")
        
        return jsonify({
            'success': False,
            'error': f'生成时间线失败: {str(e)}'
        }), 500


@app.route('/api/timeline/query/<task_id>', methods=['GET'])
def get_timeline_by_task(task_id: str):
    """
    根据任务ID获取时间线
    
    返回格式:
    {
        "success": true,
        "timeline": [...]
    }
    """
    try:
        logger.info(f"收到时间线请求，task_id: {task_id}")
        
        with task_lock:
            task = tasks.get(task_id)
            logger.info(f"任务查找结果: task存在={task is not None}, 当前任务数={len(tasks)}, 任务ID列表={list(tasks.keys())[:5]}")
        
        if not task:
            logger.warning(f"任务不存在: {task_id}")
            return jsonify({
                'success': False,
                'error': f'任务不存在: {task_id}',
                'available_tasks': list(tasks.keys())[:10] if tasks else []
            }), 404
        
        logger.info(f"任务状态: status={task.status}, has_state_data={bool(task.state_data)}, has_report={bool(task.report)}")
        
        if not task.state_data:
            logger.warning(f"任务没有状态数据: {task_id}, status={task.status}")
            return jsonify({
                'success': False,
                'error': '该任务还没有状态数据，无法生成时间线。可能原因：1) 任务还在执行中 2) 任务执行失败 3) 状态数据未保存',
                'task_status': task.status,
                'has_report': bool(task.report)
            }), 404
        
        # 生成时间线
        timeline_service = create_timeline_service()
        timeline_result = timeline_service.generate_timeline(task.state_data)
        
        if timeline_result.get("error"):
            return jsonify({
                'success': False,
                'error': timeline_result.get("error")
            }), 500
        
        return jsonify({
            'success': True,
            **timeline_result
        })
        
    except Exception as e:
        logger.exception(f"获取时间线失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'message': 'API 服务运行正常'
    })


if __name__ == '__main__':
    logger.info("启动 API 服务器...")
    app.run(host='0.0.0.0', port=6001, debug=True)

