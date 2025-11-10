"""结果展示页面"""
import streamlit as st
from api.mock_api import MockAPI
# api_client = MockAPI()
from api.api_client import api_client
from components.sidebar import render_sidebar
from utils.state import (
    init_session_state,
    set_verification_data,
    set_timeline_data
)
from loguru import logger



# 页面配置
st.set_page_config(
    page_title="分析结果 - Verum",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def render_verdict_section(verification):
    """渲染真实性判定结果"""

    st.subheader("⚖️ 新闻真假判别")
    
    if not verification:
        st.markdown('<div class="verdict-container">⏳ 正在判别新闻真假...</div>', unsafe_allow_html=True)
        return
    
    # 判定结果徽章
    verdict_colors = {
        "真": ("✅", "#d4edda", "#155724"),
        "假": ("❌", "#f8d7da", "#721c24"),
        "部分真实": ("⚠️", "#fff3cd", "#856404"),
        "无法确定": ("❓", "#e2e3e5", "#383d41")
    }
    
    emoji, bg_color, text_color = verdict_colors.get(
        verification.verdict, 
        ("❓", "#e2e3e5", "#383d41")
    )
    
    st.markdown(f"""
    <div style="
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: {bg_color};
        color: {text_color};
        margin-bottom: 0.5rem;
        font-weight: bold;
        font-size: 1.2rem;
    ">
        {emoji} {verification.verdict}
    </div>
    """, unsafe_allow_html=True)
    
    # 判别摘要
    st.markdown("**判别摘要：**")
    st.caption(verification.summary)


def render_report_tabs(report_text, current_query):
    """渲染报告标签页"""

    tab1, tab2 = st.tabs(["📰 新闻原文", "📄 AI 分析报告"])
    
    with tab1:
        # 如果是链接查询，显示原文
        if current_query.startswith("http"):
            st.components.v1.iframe(current_query, height=400, scrolling=True)
        else:
            st.info("💡 当前为主题搜索，没有单一原文链接")
            st.caption("您可以在时间线模块中查看相关新闻来源")
            st.markdown('<div class="report-container">', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="report-container">', unsafe_allow_html=True)
        if report_text:
            st.markdown(report_text)
        else:
            st.info("⏳ 报告生成中，请稍候...")
        st.markdown('</div>', unsafe_allow_html=True)


def render_feedback_section():
    """渲染反馈按钮"""
    st.markdown("### 💭 您的看法")
    
    col1, col2 = st.columns(2)
    
    # 初始化计数器
    if 'agree_count' not in st.session_state:
        st.session_state.agree_count = 42
    if 'disagree_count' not in st.session_state:
        st.session_state.disagree_count = 8
    
    with col1:
        if st.button(f"👍 认同 ({st.session_state.agree_count})", use_container_width=True):
            st.session_state.agree_count += 1
            st.rerun()
    
    with col2:
        if st.button(f"👎 不认同 ({st.session_state.disagree_count})", use_container_width=True):
            st.session_state.disagree_count += 1
            st.rerun()


def render_timeline_section(timeline_data):
    """渲染时间线"""
    
    st.subheader("📅 新闻时间线")
    
    st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
    
    if not timeline_data:
        st.info("⏳ 正在生成时间线...")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # 统计信息
    if timeline_data.date_range or timeline_data.total_sources > 0:
        col1, col2 = st.columns(2)
        with col1:
            if timeline_data.date_range:
                st.metric("时间范围", f"{timeline_data.date_range['start']} - {timeline_data.date_range['end']}")
        with col2:
            st.metric("参考文章总数", f"{timeline_data.total_sources} 篇")
        
        st.divider()
    
    # 时间线内容
    if timeline_data.timeline:
        for item in timeline_data.timeline:
            with st.expander(f"📅 {item.date} ({item.source_count}篇)", expanded=False):
                for event in item.events:
                    # 事件标题和时间
                    time_text = f" ({event.time})" if event.time else ""
                    st.markdown(f"**{event.title}**{time_text}")
                    
                    # 事件描述
                    if event.description:
                        st.caption(event.description)
                    
                    # 参考文章
                    if event.sources:
                        st.caption("**参考文章：**")
                        for source in event.sources:
                            parts = []
                            if source.url:
                                parts.append(f"[{source.title}]({source.url})")
                            else:
                                parts.append(source.title)
                            
                            if source.website_name:
                                parts.append(f"- {source.website_name}")
                            
                            if source.score:
                                parts.append(f"(相关度: {source.score:.2f})")
                            
                            st.caption(" ".join(parts))
                    
                    st.divider()
    else:
        st.info("暂无时间线事件")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_external_discussions():
    """渲染外部讨论链接"""
    st.subheader("💬 社区讨论")
    
    st.markdown('<div class="discussion-container">', unsafe_allow_html=True)
    st.caption("查看其他平台的相关讨论")
    
    # Mock 数据 - 实际应该从 API 获取
    discussions = MockAPI.get_external_discussions()
    
    for discussion in discussions:
        # 平台图标
        platform_emoji = {
            "小红书": "📕",
            "知乎": "🎓",
            "微博": "📱",
            "抖音": "🎵"
        }
        emoji = platform_emoji.get(discussion.platform, "🔗")
        
        st.markdown(f"""
        <a href="{discussion.url}" target="_blank" style="
            display: block;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            border-radius: 0.5rem;
            background-color: #f0f2f6;
            text-decoration: none;
            color: inherit;
        ">
            {emoji} <strong>{discussion.platform}</strong>: {discussion.title}
        </a>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def main():
    """主函数"""
    # 初始化
    init_session_state()
    
    # 获取历史记录并渲染侧边栏
    history = MockAPI.get_user_history()
    render_sidebar(history)
    
    # 检查是否有待处理的任务
    task_id = st.session_state.get('pending_task_id')
    current_query = st.session_state.get('current_query', '分析结果')
    
    if st.button("← 返回首页"):
        st.switch_page("app.py")

    # 页面标题
    st.title(f"📊 {current_query}")
    
    # 获取当前已加载的数据
    report_text = st.session_state.get('module_report')
    verification = st.session_state.get('module_verification')
    timeline_data = st.session_state.get('module_timeline')
    
    # === 第一步：先创建可替换的占位容器并渲染当前内容 ===

    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        verdict_placeholder = st.empty()
        with verdict_placeholder.container():
            render_verdict_section(verification)
        
        st.divider()
        
        report_placeholder = st.empty()
        with report_placeholder.container():
            render_report_tabs(report_text, current_query)
        
        st.divider()
        render_feedback_section()
    
    with right_col:
        timeline_placeholder = st.empty()
        with timeline_placeholder.container():
            render_timeline_section(timeline_data)
        
        st.divider()
        
        discussions_placeholder = st.empty()
        with discussions_placeholder.container():
            render_external_discussions()
    
    
    
    # === 第二步：后台加载数据并更新容器（不阻塞布局渲染） ===
    # 加载报告（如果还没加载）
    if task_id and not report_text:
        try:
            logger.info(f"开始生成报告: {task_id}")
            report_data = api_client.wait_for_query(task_id, poll_interval=1.0, max_wait_time=3000.0)
            
            if report_data and hasattr(report_data, 'report'):
                report_text = report_data.report
                st.session_state.module_report = report_text
                logger.info("报告生成完成")
                with report_placeholder.container():
                    render_report_tabs(report_text, current_query)
        except Exception as e:
            logger.error(f"生成报告失败: {str(e)}")
            with report_placeholder.container():
                st.markdown('<div class="report-container">', unsafe_allow_html=True)
                st.error(f"❌ 报告生成失败: {str(e)}")
                st.markdown('</div>', unsafe_allow_html=True)
            return
    
    # 加载真假判别（如果报告已加载但判别还没加载）
    if task_id and report_text and not verification:
        try:
            logger.info(f"开始判别: {task_id}")
            verification = api_client.create_verification(task_id=task_id)
            set_verification_data(verification)
            logger.info("判别完成")
            with verdict_placeholder.container():
                render_verdict_section(verification)
        except Exception as e:
            logger.error(f"判别失败: {str(e)}")
            with verdict_placeholder.container():
                st.markdown('<div class="verdict-container">❌ 判别失败，请稍后重试</div>', unsafe_allow_html=True)
            return
    
    # 加载时间线（如果判别已加载但时间线还没加载）
    if task_id and verification and not timeline_data:
        try:
            logger.info(f"开始生成时间线: {task_id}")
            timeline_data = api_client.create_timeline(task_id=task_id)
            set_timeline_data(timeline_data)
            logger.info("时间线生成完成")
            with timeline_placeholder.container():
                render_timeline_section(timeline_data)
        except Exception as e:
            logger.error(f"生成时间线失败: {str(e)}")
            with timeline_placeholder.container():
                st.markdown('<div class="timeline-container">❌ 时间线生成失败，请稍后重试</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
