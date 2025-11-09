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
    
    def create_query_task(self, query: str, mode: str = "deep") -> Dict:
        """
        创建查询任务
        
        Args:
            query: 查询内容
            mode: 思考模式，"deep"（深度思考）或 "quick"（浅度思考）
            
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
    
    def create_verification_task(self, query: str = None, report: str = None, task_id: str = None) -> Dict:
        """
        创建判罚任务
        
        Args:
            query: 原始查询内容（如果不提供task_id则必须）
            report: 研究报告内容（如果不提供task_id则必须）
            task_id: 可选的查询任务ID，如果提供则从该任务获取query和report
            
        Returns:
            包含 verification_id 和任务信息的字典
            
        Raises:
            Exception: 如果请求失败
        """
        try:
            url = f"{self.base_url}/api/verification"
            if query:
                logger.info(f"创建判罚任务: query={query[:50]}...")
            else:
                logger.info(f"创建判罚任务: task_id={task_id}")
            
            payload = {}
            if task_id:
                payload['task_id'] = task_id
            else:
                payload['query'] = query
                payload['report'] = report
            
            response = requests.post(
                url,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = f"创建判罚任务失败: HTTP {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            
            if not data.get('success'):
                error_msg = data.get('error', '未知错误')
                logger.error(f"创建判罚任务失败: {error_msg}")
                raise Exception(error_msg)
            
            verification_id = data.get('verification_id')
            logger.info(f"判罚任务创建成功: {verification_id}")
            return data
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_verification_status(self, verification_id: str) -> Dict:
        """
        获取判罚任务状态
        
        Args:
            verification_id: 判罚任务ID
            
        Returns:
            包含任务状态的字典
        """
        try:
            url = f"{self.base_url}/api/verification/{verification_id}/status"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                error_msg = f"获取判罚状态失败: HTTP {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            
            if not data.get('success'):
                error_msg = data.get('error', '未知错误')
                logger.error(f"获取判罚状态失败: {error_msg}")
                raise Exception(error_msg)
            
            return data.get('verification', {})
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_verification_result(self, verification_id: str) -> Dict:
        """
        获取判罚结果
        
        Args:
            verification_id: 判罚任务ID
            
        Returns:
            包含判罚结果的字典
            
        Raises:
            Exception: 如果任务未完成或失败
        """
        try:
            url = f"{self.base_url}/api/verification/{verification_id}"
            
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
            
            return data
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def wait_for_verification(
        self,
        verification_id: str,
        poll_interval: float = 2.0,
        max_wait_time: float = 300.0,
        progress_callback=None
    ) -> VerificationData:
        """
        等待判罚任务完成并返回结果
        
        Args:
            verification_id: 判罚任务ID
            poll_interval: 轮询间隔（秒）
            max_wait_time: 最大等待时间（秒）
            progress_callback: 进度回调函数，接收 (status, progress) 参数
            
        Returns:
            VerificationData 对象
            
        Raises:
            Exception: 如果任务失败或超时
        """
        start_time = time.time()
        
        while True:
            # 检查超时
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                logger.error(f"判罚任务超时: {verification_id}")
                raise Exception("判罚任务执行超时")
            
            # 获取任务状态
            try:
                verification = self.get_verification_status(verification_id)
                status = verification.get('status')
                progress = verification.get('progress', 0)
                
                # 调用进度回调
                if progress_callback:
                    progress_callback(status, progress)
                
                # 检查任务状态
                if status == 'completed':
                    logger.info(f"判罚任务完成: {verification_id}")
                    result = self.get_verification_result(verification_id)
                    result_data = result.get('result', {})
                    
                    # 转换为 VerificationData 对象
                    return VerificationData(
                        verdict=result_data.get('verdict', '无法确定'),
                        summary=result_data.get('summary', ''),
                        timestamp=result_data.get('timestamp')
                    )
                
                elif status == 'error':
                    error_msg = verification.get('error_message', '未知错误')
                    logger.error(f"判罚任务失败: {error_msg}")
                    raise Exception(error_msg)
                
                elif status in ['pending', 'running']:
                    # 继续等待
                    time.sleep(poll_interval)
                
                else:
                    logger.error(f"未知任务状态: {status}")
                    raise Exception(f"未知任务状态: {status}")
                    
            except Exception as e:
                logger.error(f"等待判罚结果时出错: {str(e)}")
                raise
    
    def create_timeline_task(self, state_data: Dict = None, task_id: str = None) -> Dict:
        """
        创建时间线任务
        
        Args:
            state_data: 状态数据
            task_id: 可选的查询任务ID，如果提供则从该任务获取state_data
            
        Returns:
            包含 timeline_id 和任务信息的字典
            
        Raises:
            Exception: 如果请求失败
        """
        try:
            url = f"{self.base_url}/api/timeline"
            logger.info(f"创建时间线任务...")
            
            payload = {}
            if task_id:
                payload['task_id'] = task_id
            elif state_data:
                payload['state_data'] = state_data
            else:
                raise Exception("必须提供 state_data 或 task_id")
            
            response = requests.post(
                url,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = f"创建时间线任务失败: HTTP {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            
            if not data.get('success'):
                error_msg = data.get('error', '未知错误')
                logger.error(f"创建时间线任务失败: {error_msg}")
                raise Exception(error_msg)
            
            timeline_id = data.get('timeline_id')
            logger.info(f"时间线任务创建成功: {timeline_id}")
            return data
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_timeline_status(self, timeline_id: str) -> Dict:
        """
        获取时间线任务状态
        
        Args:
            timeline_id: 时间线任务ID
            
        Returns:
            包含任务状态的字典
        """
        try:
            url = f"{self.base_url}/api/timeline/{timeline_id}/status"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                error_msg = f"获取时间线状态失败: HTTP {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            
            if not data.get('success'):
                error_msg = data.get('error', '未知错误')
                logger.error(f"获取时间线状态失败: {error_msg}")
                raise Exception(error_msg)
            
            return data.get('timeline', {})
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_timeline_result(self, timeline_id: str) -> Dict:
        """
        获取时间线结果
        
        Args:
            timeline_id: 时间线任务ID
            
        Returns:
            包含时间线结果的字典
            
        Raises:
            Exception: 如果任务未完成或失败
        """
        try:
            url = f"{self.base_url}/api/timeline/{timeline_id}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                error_msg = f"获取时间线结果失败: HTTP {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            
            if not data.get('success'):
                error_msg = data.get('error', '未知错误')
                logger.error(f"获取时间线结果失败: {error_msg}")
                raise Exception(error_msg)
            
            return data
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def wait_for_timeline(
        self,
        timeline_id: str,
        poll_interval: float = 2.0,
        max_wait_time: float = 300.0,
        progress_callback=None
    ) -> TimelineData:
        """
        等待时间线任务完成并返回结果
        
        Args:
            timeline_id: 时间线任务ID
            poll_interval: 轮询间隔（秒）
            max_wait_time: 最大等待时间（秒）
            progress_callback: 进度回调函数，接收 (status, progress) 参数
            
        Returns:
            TimelineData 对象
            
        Raises:
            Exception: 如果任务失败或超时
        """
        start_time = time.time()
        
        while True:
            # 检查超时
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                logger.error(f"时间线任务超时: {timeline_id}")
                raise Exception("时间线任务执行超时")
            
            # 获取任务状态
            try:
                timeline = self.get_timeline_status(timeline_id)
                status = timeline.get('status')
                progress = timeline.get('progress', 0)
                
                # 调用进度回调
                if progress_callback:
                    progress_callback(status, progress)
                
                # 检查任务状态
                if status == 'completed':
                    logger.info(f"时间线任务完成: {timeline_id}")
                    result = self.get_timeline_result(timeline_id)
                    result_data = result.get('result', {})
                    
                    # 转换为 TimelineData 对象
                    return self._build_timeline_data(result_data)
                
                elif status == 'error':
                    error_msg = timeline.get('error_message', '未知错误')
                    logger.error(f"时间线任务失败: {error_msg}")
                    raise Exception(error_msg)
                
                elif status in ['pending', 'running']:
                    # 继续等待
                    time.sleep(poll_interval)
                
                else:
                    logger.error(f"未知任务状态: {status}")
                    raise Exception(f"未知任务状态: {status}")
                    
            except Exception as e:
                logger.error(f"等待时间线结果时出错: {str(e)}")
                raise
    
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


# 创建全局实例
api_client = APIClient()

