"""Mock数据 - 用于开发和测试"""
from models.data_models import (
    HistoryItem, Recommendation, ReportData, ReportSource, ExternalDiscussion, 
    TimelineData, TimelineItem, TimelineEvent, TimelineSource
)


# 历史记录
MOCK_HISTORY = [
    HistoryItem(query="OpenAI 投资 AMD", timestamp="2025-11-08"),
    HistoryItem(query="美联储利率决议", timestamp="2025-11-07"),
    HistoryItem(query="中国新能源车出口", timestamp="2025-11-06"),
]


# 热点推荐
MOCK_RECOMMENDATIONS = [
    Recommendation(title="美联储最新利率决议", heat=0.91),
    Recommendation(title="中国新能源车出口激增", heat=0.84),
    Recommendation(title="OpenAI 与 AMD 合作传闻", heat=0.78),
    Recommendation(title="特斯拉新型电池技术突破", heat=0.72),
]


# 报告数据示例
MOCK_REPORT = ReportData(
    verdict="中可信",
    confidence=0.73,
    report="""# OpenAI 投资 AMD 事件分析报告

## 事件概述
近日，有消息称OpenAI计划投资AMD一千亿美元，引发广泛关注。经过溯源分析，该消息存在一定程度的误读。

## 核心事实
1. OpenAI与AMD确实在AI芯片领域有合作讨论
2. 投资金额被夸大，实际为战略合作而非巨额投资
3. 部分媒体在转载过程中混淆了"合作"与"投资"的概念

## 可信度分析
- **支持证据**: AMD官方确认正在与多家AI公司洽谈合作
- **质疑证据**: OpenAI并未发布任何关于千亿投资的官方声明
- **结论**: 该消息部分属实但被显著夸大

## 建议
建议持续关注官方渠道的后续声明，不轻信未经证实的传闻。
""",
    sources=[
        ReportSource(title="AMD 官方声明", url="https://www.amd.com/news/official-statement"),
        ReportSource(title="Bloomberg 原始报道", url="https://www.bloomberg.com/tech/amd-openai"),
        ReportSource(title="TechCrunch 分析", url="https://techcrunch.com/2025/11/08/openai-amd"),
    ]
)


# 外部讨论链接
MOCK_EXTERNAL_DISCUSSIONS = [
    ExternalDiscussion(
        platform="小红书",
        title="OpenAI投资AMD是真的吗？",
        url="https://www.xiaohongshu.com/explore/123456"
    ),
    ExternalDiscussion(
        platform="知乎",
        title="如何看待OpenAI与AMD的合作传闻？",
        url="https://www.zhihu.com/question/987654321"
    ),
    ExternalDiscussion(
        platform="微博",
        title="#OpenAI AMD# 热门讨论",
        url="https://weibo.com/search?q=OpenAI+AMD"
    ),
]


# 事件ID映射（用于快速查找）
MOCK_EVENT_MAP = {
    "evt_20251009_openai_amd": {
        "report": MOCK_REPORT,
        "discussions": MOCK_EXTERNAL_DISCUSSIONS,
    }
}

# 时间线数据示例
MOCK_TIMELINE = TimelineData(
    timeline=[
        TimelineItem(
            date="2025-11-08",
            date_key="20251108",
            events=[
                TimelineEvent(
                    title="OpenAI 投资 AMD",
                    description="OpenAI 计划投资 AMD 一千亿美元，引发广泛关注。",
                    time="2025-11-08 10:00:00", 
                    datetime="2025-11-08 10:00:00",
                    sources=[
                        TimelineSource(
                            title="AMD 官方声明",
                            url="https://www.amd.com/news/official-statement",
                            score=0.9,
                            website_name="AMD",
                            content_preview="OpenAI 计划投资 AMD 一千亿美元，引发广泛关注。"
                        )
                    ]
                )
            ],
            source_count=3
        )
    ],
    total_sources=3,
    date_range={
        "start": "2025-11-08",
        "end": "2025-11-08"
    }
)

