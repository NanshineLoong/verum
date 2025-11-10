"""数据模型定义"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict


# 首页历史记录与推荐
@dataclass
class HistoryItem:
    """历史记录项"""
    query: str
    timestamp: str


@dataclass
class Recommendation:
    """推荐新闻"""
    title: str
    heat: float


# 搜索结果与上下文
@dataclass
class SearchContext:
    """搜索上下文"""
    query: str
    type: str  # "link" or "description"
    graph_id: Optional[str] = None


# 报告页核心结构
@dataclass
class ReportSource:
    """报告来源"""
    title: str
    url: str


@dataclass
class ReportData:
    """报告数据"""
    report: str
    verdict: Optional[str] = None  # 高可信/中可信/低可信
    confidence: Optional[float] = None
    sources: List[ReportSource] = field(default_factory=list)
    verification: Optional[Dict] = None  # 新闻真假判别结果
    task: Optional[Dict] = None  # 任务信息


# 外部平台链接
@dataclass
class ExternalDiscussion:
    """外部讨论链接"""
    platform: str
    title: str
    url: str


# 新闻真假判别
@dataclass
class VerificationData:
    """判别数据"""
    verdict: str  # 真/假/部分真实/无法确定
    summary: str
    timestamp: Optional[str] = None


# 时间线
@dataclass
class TimelineSource:
    """时间线来源"""
    title: str
    url: str
    score: Optional[float] = None
    website_name: Optional[str] = None
    content_preview: Optional[str] = None


@dataclass
class TimelineEvent:
    """时间线事件"""
    title: str
    description: str
    time: Optional[str] = None
    datetime: Optional[str] = None
    sources: List[TimelineSource] = field(default_factory=list)


@dataclass
class TimelineItem:
    """时间线项"""
    date: str
    date_key: str
    events: List[TimelineEvent]
    source_count: int


@dataclass
class TimelineData:
    """时间线数据"""
    timeline: List[TimelineItem]
    total_sources: int
    date_range: Optional[Dict] = None

