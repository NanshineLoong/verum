"""API 客户端 - 对接后端 API"""
import os
import time
import requests
from typing import Dict
from loguru import logger

# 导入数据模型
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.data_models import (
    ReportData,
    VerificationData,
    TimelineData,
    TimelineItem,
    TimelineEvent,
    TimelineSource
)


class APIClient:
    """Query Engine API 客户端"""
    
    def __init__(self, base_url: str = None):
        """
        初始化 API 客户端
        
        Args:
            base_url: API 服务器地址，默认从环境变量读取或使用 http://localhost:6001
        """
        self.base_url = base_url or os.getenv("QUERY_API_BASE_URL", "http://localhost:6001")
        logger.info(f"QueryAPIClient 初始化，连接到: {self.base_url}")
    
    def get_task_status(self, task_id: str) -> Dict:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            包含任务状态的字典
        """
        try:
            url = f"{self.base_url}/api/query/{task_id}/status"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                error_msg = f"获取状态失败: HTTP {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            
            if not data.get('success'):
                error_msg = data.get('error', '未知错误')
                logger.error(f"获取状态失败: {error_msg}")
                raise Exception(error_msg)
            
            return data.get('task', {})
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_task_result(self, task_id: str) -> Dict:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            包含任务结果和报告的字典
            
        Raises:
            Exception: 如果任务未完成或失败
        """
        try:
            url = f"{self.base_url}/api/query/{task_id}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                error_msg = f"获取结果失败: HTTP {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            
            if not data.get('success'):
                error_msg = data.get('error', '未知错误')
                logger.error(f"获取结果失败: {error_msg}")
                raise Exception(error_msg)
            
            return data
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def create_query_task(self, query: str, mode: str = "auto") -> Dict:
        """
        创建查询任务
        
        Args:
            query: 查询内容
            mode: 思考模式，"deep"（深度思考）、"quick"（浅度思考）或 "auto"（自动判断，默认）
            
        Returns:
            包含 task_id 和任务信息的字典
            
        Raises:
            Exception: 如果请求失败
        """
        try:
            url = f"{self.base_url}/api/query"
            logger.info(f"创建查询任务: {query}, 模式: {mode}")
            
            response = requests.post(
                url,
                json={"query": query, "mode": mode},
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = f"创建任务失败: HTTP {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            
            if not data.get('success'):
                error_msg = data.get('error', '未知错误')
                logger.error(f"创建任务失败: {error_msg}")
                raise Exception(error_msg)
            
            task_id = data.get('task_id')
            logger.info(f"任务创建成功: {task_id}")
            return data
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def wait_for_query(
        self, 
        task_id: str, 
        poll_interval: float = 2.0,
        max_wait_time: float = 3000.0,
        progress_callback=None
    ) -> Dict:
        """
        等待查询任务完成并返回结果
        
        Args:
            task_id: 任务ID
            poll_interval: 轮询间隔（秒）
            max_wait_time: 最大等待时间（秒）
            progress_callback: 进度回调函数，接收 (status, progress) 参数
            
        Returns:
            包含 report 和 verification 的字典
            
        Raises:
            Exception: 如果任务失败或超时
        """
        start_time = time.time()
        
        while True:
            # 检查超时
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                logger.error(f"任务超时: {task_id}")
                raise Exception("任务执行超时")
            
            # 获取任务状态
            try:
                task = self.get_task_status(task_id)
                status = task.get('status')
                progress = task.get('progress', 0)
                
                # 调用进度回调
                if progress_callback:
                    progress_callback(status, progress)
                
                # 检查任务状态
                if status == 'completed':
                    logger.info(f"查询任务完成: {task_id}")
                    result = self.get_task_result(task_id)
                    return ReportData(
                        report=result.get('report'),
                        verification=result.get('verification'),
                        task=result.get('task')
                    )
                
                elif status == 'error':
                    error_msg = task.get('error_message', '未知错误')
                    logger.error(f"任务失败: {error_msg}")
                    raise Exception(error_msg)
                
                elif status in ['pending', 'running']:
                    # 继续等待
                    time.sleep(poll_interval)
                
                else:
                    logger.error(f"未知任务状态: {status}")
                    raise Exception(f"未知任务状态: {status}")
                    
            except Exception as e:
                logger.error(f"等待任务结果时出错: {str(e)}")
                raise

    def create_verification(self, task_id: str = None, query: str = None, report: str = None) -> VerificationData:
        """
        创建判罚任务（同步执行并返回结果）
        
        Args:
            task_id: 任务ID（如果提供，则从该任务获取query和report）
            query: 原始查询内容（如果不提供task_id则必须）
            report: 研究报告内容（如果不提供task_id则必须）
            
        Returns:
            VerificationData 对象
            
        Raises:
            Exception: 如果判罚失败
        """
        try:
            url = f"{self.base_url}/api/verification"
            
            payload = {}
            if task_id:
                payload['task_id'] = task_id
            else:
                if not query or not report:
                    raise Exception("必须提供 task_id 或 (query + report)")
                payload['query'] = query
                payload['report'] = report
            
            logger.info(f"创建判罚任务: task_id={task_id}")
            
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code != 200:
                error_msg = f"判罚失败: HTTP {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            
            if not data.get('success'):
                error_msg = data.get('error', '未知错误')
                logger.error(f"判罚失败: {error_msg}")
                raise Exception(error_msg)
            
            result_data = data.get('verification', {})
            
            # 转换为 VerificationData 对象
            return VerificationData(
                verdict=result_data.get('verdict', '无法确定'),
                summary=result_data.get('summary', ''),
                timestamp=result_data.get('timestamp')
            )
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_verification_by_task(self, task_id: str) -> VerificationData:
        """
        根据任务ID获取判罚结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            VerificationData 对象
            
        Raises:
            Exception: 如果获取失败
        """
        try:
            url = f"{self.base_url}/api/verification/query/{task_id}"
            
            logger.info(f"获取判罚结果: task_id={task_id}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                error_msg = f"获取判罚结果失败: HTTP {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            
            if not data.get('success'):
                error_msg = data.get('error', '未知错误')
                logger.error(f"获取判罚结果失败: {error_msg}")
                raise Exception(error_msg)
            
            result_data = data.get('verification', {})
            
            # 转换为 VerificationData 对象
            return VerificationData(
                verdict=result_data.get('verdict', '无法确定'),
                summary=result_data.get('summary', ''),
                timestamp=result_data.get('timestamp')
            )
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def create_timeline(self, task_id: str = None, state_data: Dict = None) -> TimelineData:
        """
        创建时间线（同步执行并返回结果）
        
        Args:
            task_id: 任务ID（如果提供，则从该任务获取state_data）
            state_data: 状态数据（如果不提供task_id则必须）
            
        Returns:
            TimelineData 对象
            
        Raises:
            Exception: 如果生成失败
        """
        try:
            url = f"{self.base_url}/api/timeline/generate"
            
            payload = {}
            if task_id:
                payload['task_id'] = task_id
            elif state_data:
                payload['state_data'] = state_data
            else:
                raise Exception("必须提供 task_id 或 state_data")
            
            logger.info(f"创建时间线: task_id={task_id}")
            
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code != 200:
                error_msg = self._extract_error_message(
                    response,
                    default=f"生成时间线失败: HTTP {response.status_code}"
                )
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            
            if not data.get('success'):
                error_msg = data.get('error', '未知错误')
                logger.error(f"生成时间线失败: {error_msg}")
                raise Exception(error_msg)
            
            # 转换为 TimelineData 对象
            return self._build_timeline_data(data)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_timeline_by_task(self, task_id: str) -> TimelineData:
        """
        根据任务ID获取时间线
        
        Args:
            task_id: 任务ID
            
        Returns:
            TimelineData 对象
            
        Raises:
            Exception: 如果获取失败
        """
        try:
            url = f"{self.base_url}/api/timeline/query/{task_id}"
            
            logger.info(f"获取时间线: task_id={task_id}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                error_msg = f"获取时间线失败: HTTP {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            
            if not data.get('success'):
                error_msg = data.get('error', '未知错误')
                logger.error(f"获取时间线失败: {error_msg}")
                raise Exception(error_msg)
            
            # 转换为 TimelineData 对象
            return self._build_timeline_data(data)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    
    def _build_timeline_data(self, timeline_dict: Dict) -> TimelineData:
        """
        将时间线字典转换为 TimelineData 对象
        
        Args:
            timeline_dict: 时间线数据字典
            
        Returns:
            TimelineData 对象
        """
        timeline_items = []
        for item_dict in timeline_dict.get('timeline', []):
            events = []
            for event_dict in item_dict.get('events', []):
                sources = [
                    TimelineSource(
                        title=s.get('title', ''),
                        url=s.get('url', ''),
                        score=s.get('score'),
                        website_name=s.get('website_name'),
                        content_preview=s.get('content_preview')
                    )
                    for s in event_dict.get('sources', [])
                ]
                events.append(TimelineEvent(
                    title=event_dict.get('title', ''),
                    description=event_dict.get('description', ''),
                    time=event_dict.get('time'),
                    datetime=event_dict.get('datetime'),
                    sources=sources
                ))
            
            timeline_items.append(TimelineItem(
                date=item_dict.get('date', ''),
                date_key=item_dict.get('date_key', ''),
                events=events,
                source_count=item_dict.get('source_count', 0)
            ))
        
        return TimelineData(
            timeline=timeline_items,
            total_sources=timeline_dict.get('total_sources', 0),
            date_range=timeline_dict.get('date_range')
        )

    def create_mermaid_timeline(self, task_id: str = None, query: str = None, report: str = None) -> str:
        """
        创建 Mermaid Timeline（同步执行并返回结果）
        
        Args:
            task_id: 任务ID（如果提供，则从该任务获取query和report）
            query: 原始查询内容（如果不提供task_id则必须）
            report: 研究报告内容（如果不提供task_id则必须）
            
        Returns:
            Mermaid Timeline 格式的字符串
            
        Raises:
            Exception: 如果生成失败
        """
        try:
            url = f"{self.base_url}/api/timeline/mermaid"
            
            payload = {}
            if task_id:
                payload['task_id'] = task_id
            else:
                if not query or not report:
                    raise Exception("必须提供 task_id 或 (query + report)")
                payload['query'] = query
                payload['report'] = report
            
            logger.info(f"创建 Mermaid Timeline: task_id={task_id}")
            
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code != 200:
                error_msg = self._extract_error_message(
                    response,
                    default=f"生成 Mermaid Timeline 失败: HTTP {response.status_code}"
                )
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            
            if not data.get('success'):
                error_msg = data.get('error', '未知错误')
                logger.error(f"生成 Mermaid Timeline 失败: {error_msg}")
                raise Exception(error_msg)
            
            timeline_content = data.get('timeline', '')
            logger.info(f"Mermaid Timeline 生成成功，长度: {len(timeline_content)}")
            
            return timeline_content
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    @staticmethod
    def _extract_error_message(response: requests.Response, default: str) -> str:
        """
        尝试从响应体中解析错误信息
        """
        try:
            data = response.json()
            return data.get('error', default)
        except ValueError:
            return default


# 创建全局实例
api_client = APIClient()

