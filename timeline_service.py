"""
时间线生成服务
从搜索结果中提取信息，按时间线组织事件
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict
from loguru import logger

# 添加路径以便导入
sys.path.insert(0, os.path.dirname(__file__))


class TimelineService:
    """时间线生成服务"""
    
    def __init__(self):
        """初始化时间线服务"""
        logger.info("时间线服务已初始化")
    
    def generate_timeline(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        从状态数据生成时间线
        
        Args:
            state_data: 状态字典（包含paragraphs和search_history）
            
        Returns:
            时间线字典
        """
        try:
            # 提取所有搜索结果
            all_searches = self._extract_all_searches(state_data)
            
            if not all_searches:
                return {
                    "timeline": [],
                    "total_sources": 0,
                    "date_range": None,
                    "message": "没有找到搜索结果"
                }
            
            # 处理日期并排序
            processed_searches = self._process_dates(all_searches)
            
            # 按日期分组
            grouped_by_date = self._group_by_date(processed_searches)
            
            # 生成时间线结构
            timeline = self._build_timeline(grouped_by_date)
            
            # 计算统计信息
            date_range = self._calculate_date_range(processed_searches)
            
            return {
                "timeline": timeline,
                "total_sources": len(all_searches),
                "date_range": date_range,
                "message": "时间线生成成功"
            }
            
        except Exception as e:
            logger.error(f"生成时间线失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "timeline": [],
                "total_sources": 0,
                "date_range": None,
                "error": str(e),
                "message": f"生成时间线时发生错误: {str(e)}"
            }
    
    def _extract_all_searches(self, state_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从状态数据中提取所有搜索结果
        
        Args:
            state_data: 状态字典
            
        Returns:
            搜索结果列表
        """
        all_searches = []
        
        # 从paragraphs中提取
        paragraphs = state_data.get("paragraphs", [])
        for paragraph in paragraphs:
            research = paragraph.get("research", {})
            search_history = research.get("search_history", [])
            
            for search in search_history:
                # 转换为统一格式
                search_item = {
                    "title": search.get("title", ""),
                    "url": search.get("url", ""),
                    "content": search.get("content", ""),
                    "score": search.get("score"),
                    "published_date": search.get("published_date"),
                    "timestamp": search.get("timestamp"),
                    "website_name": search.get("website_name"),
                    "query": search.get("query", "")
                }
                all_searches.append(search_item)
        
        return all_searches
    
    def _process_dates(self, searches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理日期和时间信息，统一格式
        
        Args:
            searches: 搜索结果列表
            
        Returns:
            处理后的搜索结果列表
        """
        processed = []
        
        for search in searches:
            # 优先使用 published_date，如果没有则使用 timestamp
            date_str = search.get("published_date") or search.get("timestamp")
            
            if date_str:
                # 尝试解析日期和时间
                normalized_datetime = self._normalize_datetime(date_str)
                if normalized_datetime:
                    search["normalized_datetime"] = normalized_datetime
                    search["normalized_date"] = normalized_datetime[:10]  # YYYY-MM-DD
                    search["normalized_time"] = normalized_datetime[11:19] if len(normalized_datetime) > 10 else None  # HH:MM:SS
                    search["display_date"] = self._format_display_date(normalized_datetime[:10])
                    search["display_time"] = self._format_display_time(normalized_datetime[11:19]) if len(normalized_datetime) > 10 else None
                else:
                    search["normalized_datetime"] = None
                    search["normalized_date"] = None
                    search["normalized_time"] = None
                    search["display_date"] = "未知日期"
                    search["display_time"] = None
            else:
                search["normalized_datetime"] = None
                search["normalized_date"] = None
                search["normalized_time"] = None
                search["display_date"] = "未知日期"
                search["display_time"] = None
            
            processed.append(search)
        
        return processed
    
    def _normalize_datetime(self, date_str: str) -> Optional[str]:
        """
        标准化日期时间格式为 YYYY-MM-DDTHH:MM:SS
        
        Args:
            date_str: 原始日期时间字符串
            
        Returns:
            标准化后的日期时间字符串 (YYYY-MM-DDTHH:MM:SS) 或 None
        """
        if not date_str:
            return None
        
        # 尝试多种日期时间格式
        datetime_formats = [
            "%Y-%m-%dT%H:%M:%S",      # 2025-08-08T10:30:00
            "%Y-%m-%dT%H:%M:%S.%f",   # 2025-08-08T10:30:00.123456
            "%Y-%m-%d %H:%M:%S",      # 2025-08-08 10:30:00
            "%Y-%m-%d %H:%M:%S.%f",   # 2025-08-08 10:30:00.123456
            "%Y-%m-%d",               # 2025-08-08
            "%Y/%m/%d %H:%M:%S",      # 2025/08/08 10:30:00
            "%Y/%m/%d",               # 2025/08/08
            "%Y.%m.%d %H:%M:%S",      # 2025.08.08 10:30:00
            "%Y.%m.%d",               # 2025.08.08
        ]
        
        for fmt in datetime_formats:
            try:
                dt = datetime.strptime(date_str[:len(fmt)], fmt)
                return dt.strftime("%Y-%m-%dT%H:%M:%S")
            except (ValueError, IndexError):
                continue
        
        # 如果都失败，尝试提取日期时间部分
        try:
            import re
            # 尝试提取 YYYY-MM-DD HH:MM:SS 格式
            match = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})', date_str)
            if match:
                return f"{match.group(1)}T{match.group(2)}"
            # 尝试提取 YYYY-MM-DD 格式
            match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
            if match:
                return f"{match.group(1)}T00:00:00"
        except:
            pass
        
        return None
    
    def _format_display_date(self, date_str: Optional[str]) -> str:
        """
        格式化显示日期为 YYYY.MM.DD
        
        Args:
            date_str: 日期字符串 (YYYY-MM-DD)
            
        Returns:
            格式化后的日期字符串 (YYYY.MM.DD)
        """
        if not date_str:
            return "未知日期"
        
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%Y.%m.%d")
        except:
            return date_str.replace("-", ".")
    
    def _format_display_time(self, time_str: Optional[str]) -> Optional[str]:
        """
        格式化显示时间为 HH:MM
        
        Args:
            time_str: 时间字符串 (HH:MM:SS)
            
        Returns:
            格式化后的时间字符串 (HH:MM) 或 None
        """
        if not time_str:
            return None
        
        try:
            # 如果包含秒，只取时分
            if len(time_str) >= 5:
                return time_str[:5]  # HH:MM
            return time_str
        except:
            return time_str
    
    def _group_by_date(self, searches: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        按日期分组搜索结果，并在每个日期组内按相关度倒序排列
        
        Args:
            searches: 搜索结果列表
            
        Returns:
            按日期分组的字典，每个日期组内的搜索结果按相关度倒序排列（相关度高的在前）
        """
        grouped = defaultdict(list)
        
        for search in searches:
            date_key = search.get("normalized_date") or "unknown"
            grouped[date_key].append(search)
        
        # 在每个日期组内，按相关度（score）倒序排列（相关度高的在前）
        for date_key in grouped:
            grouped[date_key].sort(
                key=lambda x: (x.get("score") or 0, x.get("normalized_datetime") or ""),  # 先按相关度，再按时间作为次要排序
                reverse=True  # 倒序：相关度高的在前
            )
        
        return dict(grouped)
    
    def _build_timeline(self, grouped_by_date: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        构建时间线结构，按日期倒序排列（最新的日期在前）
        
        Args:
            grouped_by_date: 按日期分组的搜索结果（每个日期组内已按相关度倒序）
            
        Returns:
            时间线列表（按日期倒序）
        """
        timeline = []
        
        # 按日期倒序排序（最新的日期在前，未知日期放在最后）
        sorted_dates = sorted(
            [d for d in grouped_by_date.keys() if d != "unknown"],
            reverse=True  # 倒序：最新的日期在前
        )
        
        if "unknown" in grouped_by_date:
            sorted_dates.append("unknown")
        
        for date_key in sorted_dates:
            searches = grouped_by_date[date_key]
            
            # 生成事件（每个搜索结果作为一个事件，已按相关度倒序）
            events = []
            for search in searches:
                event = {
                    "title": search.get("title", "无标题"),
                    "description": search.get("content", "")[:200] + "..." if len(search.get("content", "")) > 200 else search.get("content", ""),
                    "time": search.get("display_time"),  # 显示时间
                    "datetime": search.get("normalized_datetime"),  # 完整日期时间用于排序
                    "sources": [{
                        "title": search.get("title", "无标题"),
                        "url": search.get("url", ""),
                        "score": search.get("score"),
                        "website_name": search.get("website_name"),  # 网站名称
                        "content_preview": search.get("content", "")[:150] + "..." if len(search.get("content", "")) > 150 else search.get("content", "")
                    }]
                }
                events.append(event)
            
            timeline_item = {
                "date": self._format_display_date(date_key) if date_key != "unknown" else "未知日期",
                "date_key": date_key,
                "events": events,
                "source_count": len(searches)
            }
            
            timeline.append(timeline_item)
        
        return timeline
    
    def _calculate_date_range(self, searches: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
        """
        计算日期范围
        
        Args:
            searches: 搜索结果列表
            
        Returns:
            日期范围字典
        """
        dates = [s.get("normalized_date") for s in searches if s.get("normalized_date")]
        
        if not dates:
            return None
        
        dates_sorted = sorted(dates)
        
        return {
            "start": self._format_display_date(dates_sorted[0]),
            "end": self._format_display_date(dates_sorted[-1])
        }
    
    def format_timeline_markdown(self, timeline_data: Dict[str, Any]) -> str:
        """
        将时间线数据格式化为Markdown
        
        Args:
            timeline_data: 时间线数据字典
            
        Returns:
            Markdown格式的时间线
        """
        timeline = timeline_data.get("timeline", [])
        total_sources = timeline_data.get("total_sources", 0)
        date_range = timeline_data.get("date_range")
        
        md_lines = ["## 📅 参考新闻时间线\n"]
        
        if date_range:
            md_lines.append(f"**时间范围**: {date_range.get('start')} - {date_range.get('end')}  ")
            md_lines.append(f"**参考文章总数**: {total_sources}  \n")
        
        md_lines.append("---\n")
        
        for item in timeline:
            date = item.get("date", "未知日期")
            events = item.get("events", [])
            source_count = item.get("source_count", 0)
            
            md_lines.append(f"\n### {date} ({source_count}篇)\n")
            
            for event in events:
                title = event.get("title", "无标题")
                description = event.get("description", "")
                time = event.get("time")
                sources = event.get("sources", [])
                
                # 显示标题和时间
                time_text = f" ({time})" if time else ""
                md_lines.append(f"\n**{title}**{time_text}\n")
                
                if description:
                    md_lines.append(f"{description}\n")
                
                md_lines.append("**参考文章：**\n")
                for source in sources:
                    source_title = source.get("title", "无标题")
                    source_url = source.get("url", "")
                    website_name = source.get("website_name")
                    score = source.get("score")
                    
                    # 构建显示文本：标题 - 网站名称 (相关度)
                    parts = []
                    if source_url:
                        parts.append(f"[{source_title}]({source_url})")
                    else:
                        parts.append(source_title)
                    
                    if website_name:
                        parts.append(f" - {website_name}")
                    
                    if score:
                        parts.append(f" (相关度: {score:.2f})")
                    
                    md_lines.append(f"- {' '.join(parts)}\n")
                
                md_lines.append("\n")
            
            md_lines.append("---\n")
        
        return "".join(md_lines)


def create_timeline_service() -> TimelineService:
    """
    创建时间线服务实例的便捷函数
    
    Returns:
        TimelineService实例
    """
    return TimelineService()

