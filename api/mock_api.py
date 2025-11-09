"""Mock API - 模拟后端API接口"""
import time
from typing import List, Dict, Optional
from models.data_models import (
    HistoryItem, Recommendation, ReportData, 
    ExternalDiscussion
)
from mock_data.sample_data import (
    MOCK_HISTORY, MOCK_RECOMMENDATIONS, MOCK_EVENT_MAP
)


class MockAPI:
    """Mock API类 - 模拟真实API调用"""
    
    # 模拟任务开始时间（用于计算进度）
    _task_start_times = {}
    
    @staticmethod
    def _get_mock_status(task_id: str, module_name: str, total_seconds: float) -> Dict:
        """
        获取模拟的模块状态
        
        Args:
            task_id: 任务ID
            module_name: 模块名称
            total_seconds: 完成所需的总秒数
            
        Returns:
            状态字典 {"status": "pending|running|completed", "progress": 0-100}
        """
        # 初始化任务开始时间
        if task_id not in MockAPI._task_start_times:
            MockAPI._task_start_times[task_id] = time.time()
        
        # 计算经过的时间
        elapsed = time.time() - MockAPI._task_start_times[task_id]
        
        # 根据不同模块设置不同的延迟
        delays = {
            "report": 0,      # 立即开始
            "discussion": 3   # 3秒后开始
        }
        
        delay = delays.get(module_name, 0)
        
        if elapsed < delay:
            return {"status": "pending", "progress": 0}
        
        # 计算进度
        actual_elapsed = elapsed - delay
        progress = min(100, int((actual_elapsed / total_seconds) * 100))
        
        if progress >= 100:
            return {"status": "completed", "progress": 100}
        else:
            return {"status": "running", "progress": progress}
    
    @staticmethod
    def get_user_history() -> List[HistoryItem]:
        """获取用户历史记录"""
        time.sleep(0.3)  # 模拟网络延迟
        return MOCK_HISTORY
    
    @staticmethod
    def get_recommendations() -> List[Recommendation]:
        """获取推荐新闻"""
        time.sleep(0.3)
        return MOCK_RECOMMENDATIONS
    
    @staticmethod
    def create_query_task(query: str, mode: str = "deep") -> Dict:
        """创建查询任务"""
        time.sleep(0.3)
        return {"task_id": "task_20251108_openai_amd"}
    
    @staticmethod
    def get_report(graph_id: str) -> Optional[ReportData]:
        """获取报告数据"""
        time.sleep(0.4)
        event = MOCK_EVENT_MAP.get(graph_id)
        return event["report"] if event else None
    
    
    @staticmethod
    def get_external_discussions(graph_id: str) -> List[ExternalDiscussion]:
        """获取外部平台讨论链接"""
        time.sleep(0.3)
        event = MOCK_EVENT_MAP.get(graph_id)
        return event["discussions"] if event else []
    
    @staticmethod
    def get_report_status(task_id: str) -> Dict:
        """获取报告生成状态"""
        return MockAPI._get_mock_status(task_id, "report", 5.0)
    
    @staticmethod
    def get_discussion_status(task_id: str) -> Dict:
        """获取外部讨论数据状态"""
        return MockAPI._get_mock_status(task_id, "discussion", 2.0)
    
    @staticmethod
    def wait_for_report(
        task_id: str,
        poll_interval: float = 1.0,
        max_wait_time: float = 60.0,
        progress_callback=None
    ) -> Optional[ReportData]:
        """
        等待报告生成完成
        
        Args:
            task_id: 任务ID
            poll_interval: 轮询间隔（秒）
            max_wait_time: 最大等待时间（秒）
            progress_callback: 进度回调函数，接收 (status, progress) 参数
            
        Returns:
            报告数据，如果失败则返回 None
        """
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                return None
            
            status_data = MockAPI.get_report_status(task_id)
            status = status_data.get('status')
            progress = status_data.get('progress', 0)
            
            if progress_callback:
                progress_callback(progress)
            
            if status == 'completed':
                return MockAPI.get_report(task_id)
            elif status == 'error':
                return None
            
            time.sleep(poll_interval)
    
    
    @staticmethod
    def wait_for_discussion(
        task_id: str,
        poll_interval: float = 1.0,
        max_wait_time: float = 60.0,
        progress_callback=None
    ) -> Optional[List[ExternalDiscussion]]:
        """
        等待外部讨论数据加载完成
        
        Args:
            task_id: 任务ID
            poll_interval: 轮询间隔（秒）
            max_wait_time: 最大等待时间（秒）
            progress_callback: 进度回调函数，接收 (status, progress) 参数
            
        Returns:
            外部讨论列表，如果失败则返回 None
        """
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                return None
            
            status_data = MockAPI.get_discussion_status(task_id)
            status = status_data.get('status')
            progress = status_data.get('progress', 0)
            
            if progress_callback:
                progress_callback(status, progress)
            
            if status == 'completed':
                return MockAPI.get_external_discussions(task_id)
            elif status == 'error':
                return None
            
            time.sleep(poll_interval)

