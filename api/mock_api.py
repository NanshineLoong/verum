"""Mock API - 模拟后端API接口"""
import time
from typing import List, Dict
from models.data_models import (
    HistoryItem, Recommendation, ExternalDiscussion,
    VerificationData, TimelineData
)
from mock_data.sample_data import (
    MOCK_HISTORY, MOCK_RECOMMENDATIONS, MOCK_REPORT,
    MOCK_VERIFICATION, MOCK_TIMELINE, MOCK_EXTERNAL_DISCUSSIONS
)


class MockAPI:
    """Mock API类 - 完全模拟 api_client.py 的接口"""
    
    # 任务开始时间跟踪
    _task_start_times = {}
    
    @staticmethod
    def _get_task_progress(task_id: str, task_type: str) -> Dict:
        """
        计算任务进度
        
        Args:
            task_id: 任务ID
            task_type: 任务类型 (query/verification/timeline)
            
        Returns:
            {"status": "pending|running|completed", "progress": 0-100}
        """
        # 初始化任务开始时间
        if task_id not in MockAPI._task_start_times:
            MockAPI._task_start_times[task_id] = time.time()
        
        elapsed = time.time() - MockAPI._task_start_times[task_id]
        
        # 不同任务类型的配置：(延迟开始秒数, 总耗时秒数)
        task_configs = {
            "query": (0, 10.0),          # 立即开始，10秒完成
            "verification": (2.0, 5.0),  # 2秒后开始，5秒完成
            "timeline": (4.0, 3.0)       # 4秒后开始，3秒完成
        }
        
        delay, duration = task_configs.get(task_type, (0, 5.0))
        
        # 延迟阶段
        if elapsed < delay:
            return {"status": "pending", "progress": 0}
        
        # 运行阶段
        actual_elapsed = elapsed - delay
        progress = min(100, int((actual_elapsed / duration) * 100))
        
        if progress >= 100:
            return {"status": "completed", "progress": 100}
        else:
            return {"status": "running", "progress": progress}
    
    # ==================== 基础数据接口 ====================
    
    @staticmethod
    def get_user_history() -> List[HistoryItem]:
        """获取用户历史记录"""
        time.sleep(0.1)
        return MOCK_HISTORY
    
    @staticmethod
    def get_recommendations() -> List[Recommendation]:
        """获取推荐新闻"""
        time.sleep(0.1)
        return MOCK_RECOMMENDATIONS
    
    @staticmethod
    def get_external_discussions() -> List[ExternalDiscussion]:
        """获取外部平台讨论链接"""
        time.sleep(0.1)
        return MOCK_EXTERNAL_DISCUSSIONS
    
    # ==================== Query 任务接口 ====================
    
    @staticmethod
    def create_query_task(query: str, mode: str = "deep") -> Dict:
        """
        创建查询任务
        
        Args:
            query: 查询内容
            mode: 思考模式
            
        Returns:
            {"success": True, "task_id": "...", "message": "...", "task": {...}}
        """
        time.sleep(0.2)
        task_id = f"query_{int(time.time())}"
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "查询任务已创建",
            "task": {
                "task_id": task_id,
                "query": query,
                "mode": mode,
                "status": "pending",
                "progress": 0,
                "error_message": "",
                "has_result": False,
                "has_verification": False,
                "has_timeline": False
            }
        }
    
    @staticmethod
    def get_task_status(task_id: str) -> Dict:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态字典
        """
        time.sleep(0.05)
        status_data = MockAPI._get_task_progress(task_id, "query")
        
        return {
            "task_id": task_id,
            "status": status_data["status"],
            "progress": status_data["progress"],
            "error_message": "",
            "has_result": status_data["status"] == "completed"
        }
    
    @staticmethod
    def get_task_result(task_id: str) -> Dict:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            {"success": True, "task": {...}, "report": "...", "verification": {...}}
        """
        time.sleep(0.1)
        
        return {
            "success": True,
            "task": {
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "has_result": True
            },
            "report": MOCK_REPORT,
            "verification": {
                "verdict": MOCK_VERIFICATION.verdict,
                "summary": MOCK_VERIFICATION.summary,
                "timestamp": MOCK_VERIFICATION.timestamp
            }
        }
    
    # ==================== Verification 任务接口 ====================
    
    @staticmethod
    def create_verification(query: str = None, report: str = None, task_id: str = None) -> VerificationData:
        """
        创建判罚任务（同步执行并返回结果）
        
        Args:
            query: 原始查询内容
            report: 研究报告内容
            task_id: 可选的查询任务ID
            
        Returns:
            VerificationData 对象
        """
        time.sleep(1.0)  # 模拟判罚耗时
        return MOCK_VERIFICATION
    
    @staticmethod
    def get_verification_by_task(task_id: str) -> VerificationData:
        """
        根据任务ID获取判罚结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            VerificationData 对象
        """
        time.sleep(0.1)
        return MOCK_VERIFICATION
    
    # ==================== Timeline 任务接口 ====================
    
    @staticmethod
    def create_timeline(state_data: Dict = None, task_id: str = None) -> TimelineData:
        """
        创建时间线（同步执行并返回结果）
        
        Args:
            state_data: 状态数据
            task_id: 可选的查询任务ID
            
        Returns:
            TimelineData 对象
        """
        time.sleep(1.0)  # 模拟时间线生成耗时
        return MOCK_TIMELINE
    
    @staticmethod
    def get_timeline_by_task(task_id: str) -> TimelineData:
        """
        根据任务ID获取时间线
        
        Args:
            task_id: 任务ID
            
        Returns:
            TimelineData 对象
        """
        time.sleep(0.1)
        return MOCK_TIMELINE
    
    # ==================== 等待方法（模拟轮询）====================
    
    @staticmethod
    def wait_for_query(
        task_id: str,
        poll_interval: float = 1.0,
        max_wait_time: float = 60.0,
        progress_callback=None
    ):
        """等待查询任务完成并返回 ReportData 对象"""
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                raise Exception("任务执行超时")
            
            task = MockAPI.get_task_status(task_id)
            status = task.get('status')
            progress = task.get('progress', 0)
            
            if progress_callback:
                progress_callback(status, progress)
            
            if status == 'completed':
                result = MockAPI.get_task_result(task_id)
                # 导入 ReportData 并返回对象而不是字典
                from models.data_models import ReportData
                return ReportData(
                    report=result.get('report'),
                    verification=result.get('verification'),
                    task=result.get('task')
                )
            elif status == 'error':
                raise Exception(task.get('error_message', '未知错误'))
            
            time.sleep(poll_interval)
