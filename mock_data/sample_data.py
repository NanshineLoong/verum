"""Mock数据 - 用于开发和测试"""
from models.data_models import (
    HistoryItem, Recommendation, ReportData, ReportSource, ExternalDiscussion,
    VerificationData, TimelineData, TimelineItem, TimelineEvent, TimelineSource
)


# 历史记录
MOCK_HISTORY = [
    HistoryItem(query="OpenAI 投资 AMD", timestamp="2025-11-08"),
    HistoryItem(query="美联储利率决议", timestamp="2025-11-07"),
    HistoryItem(query="中国新能源车出口", timestamp="2025-11-06"),
]


# 热点推荐
MOCK_RECOMMENDATIONS = [
    Recommendation(title="DeepSeek研究员称AI可能长期取代大部分人类工作", heat=0.91),
    Recommendation(title="FAA因人手短缺对纽瓦克机场下达停飞命令", heat=0.84),
    Recommendation(title="胖东来销售额破纪录，比去年全年高出30亿元", heat=0.78),
    Recommendation(title="谷歌新技术一键推演微积分，或将终结PS时代", heat=0.72),
]


# 报告数据示例
MOCK_REPORT = """# OpenAI 投资 AMD 事件分析报告

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

## 参考来源
1. AMD 官方声明 - [链接](https://www.amd.com/news)
2. Bloomberg 原始报道 - [链接](https://www.bloomberg.com)
3. TechCrunch 分析 - [链接](https://techcrunch.com)

## 建议
建议持续关注官方渠道的后续声明，不轻信未经证实的传闻。
"""


# 判罚数据示例
MOCK_VERIFICATION = VerificationData(
    verdict="部分真实",
    summary='经过对多方信息源的分析，OpenAI与AMD确实存在合作洽谈，但"投资一千亿美元"的说法缺乏官方证实，存在媒体夸大和误读的情况。建议将此消息标记为"部分真实"。',
    timestamp="2025-11-08 15:30:00"
)


# 时间线数据示例
MOCK_TIMELINE = TimelineData(
    timeline=[
        TimelineItem(
            date="2025.11.08",
            date_key="2025-11-08",
            events=[
                TimelineEvent(
                    title="AMD官方回应合作传闻",
                    description="AMD发布声明确认正在与多家AI公司进行战略合作讨论，但未透露具体投资金额。",
                    time="14:30",
                    datetime="2025-11-08T14:30:00",
                    sources=[
                        TimelineSource(
                            title="AMD官方声明：关于AI芯片合作的说明",
                            url="https://www.amd.com/news/official-statement",
                            score=0.95,
                            website_name="AMD官网",
                            content_preview="AMD确认正在与包括OpenAI在内的多家公司讨论AI芯片合作事宜..."
                        )
                    ]
                ),
                TimelineEvent(
                    title="Bloomberg首次报道合作消息",
                    description="Bloomberg报道称OpenAI正在与AMD洽谈AI芯片供应合作，涉及金额可能达到数十亿美元。",
                    time="10:15",
                    datetime="2025-11-08T10:15:00",
                    sources=[
                        TimelineSource(
                            title="OpenAI in Talks with AMD for AI Chip Partnership",
                            url="https://www.bloomberg.com/tech/amd-openai-2025",
                            score=0.92,
                            website_name="Bloomberg",
                            content_preview="Sources say OpenAI is negotiating with AMD for a potential multi-billion dollar chip deal..."
                        )
                    ]
                )
            ],
            source_count=2
        ),
        TimelineItem(
            date="2025.11.07",
            date_key="2025-11-07",
            events=[
                TimelineEvent(
                    title="科技博主率先曝光消息",
                    description="多位科技领域博主在社交媒体上曝光OpenAI可能投资AMD的消息，引发热议。",
                    time="20:45",
                    datetime="2025-11-07T20:45:00",
                    sources=[
                        TimelineSource(
                            title="科技博主爆料：OpenAI将投资AMD",
                            url="https://twitter.com/techblogger/status/123456",
                            score=0.68,
                            website_name="Twitter",
                            content_preview="独家消息：OpenAI计划向AMD投资千亿美元，布局AI芯片..."
                        )
                    ]
                )
            ],
            source_count=1
        )
    ],
    total_sources=3,
    date_range={
        "start": "2025.11.07",
        "end": "2025.11.08"
    }
)


# 外部讨论链接
MOCK_EXTERNAL_DISCUSSIONS = [
    ExternalDiscussion(
        platform="小红书",
        title="OpenAI投资AMD是真的吗？深度解析",
        url="https://www.xiaohongshu.com/user/profile/5d0bb58f00000000110378bd"
    ),
    ExternalDiscussion(
        platform="知乎",
        title="如何看待OpenAI与AMD的合作传闻？",
        url="https://www.zhihu.com/"
    ),
    ExternalDiscussion(
        platform="微博",
        title="#OpenAI AMD# 最新进展讨论",
        url="https://weibo.com/"
    ),
    ExternalDiscussion(
        platform="抖音",
        title="一分钟看懂OpenAI和AMD的关系",
        url="https://www.douyin.com/"
    ),
]

# Mermaid Timeline 数据示例
MOCK_MERMAID_TIMELINE = """timeline
    title OpenAI-AMD合作事件线
    2025-10-06 : 正式宣布战略合作
               : AMD官方声明
               : 5年期6GW算力部署
    2025-10-07 : 传闻传播期
               : 社交媒体"千亿美元"传闻
               : AMD股价暴涨+43%
    2025-10-18 : 合作扩展
               : 纳入博通等供应商
    2025-11-04 : 财报发布
               : Q3营收92.5亿美元
               : 股价回调-3.9%
    2025-11-07 : 政策影响
               : OpenAI谈政府担保
               : 科技股市值蒸发5000亿
    2025-11-09 : 事实核查
               : 确认传闻失实"""
