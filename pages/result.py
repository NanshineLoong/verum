"""结果展示页面"""
import streamlit as st
import time
from api.mock_api import MockAPI
from api.api_client import api_client
from components.sidebar import render_sidebar
from utils.state import init_session_state
from loguru import logger


api_client = api_client

# 页面配置
st.set_page_config(
    page_title="分析结果 - Verum",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# 左上
def render_verdict_section(pending_task_id):
    """渲染真实性判定和判别结果"""
    # 获取判别数据
    verification_data = st.session_state.get('module_verification')
    if not verification_data and pending_task_id:
        try:
            verification = api_client.wait_for_verification(pending_task_id)
            
        except Exception as e:
            logger.warning(f"加载判别结果失败: {str(e)}")
    
    if not verification_data:
        return
    
    st.subheader("⚖️ 新闻真假判别")
    
    # 判定结果徽章
    verdict_colors = {
        "真": ("✅", "#d4edda", "#155724"),
        "假": ("❌", "#f8d7da", "#721c24"),
        "部分真实": ("⚠️", "#fff3cd", "#856404"),
        "无法确定": ("❓", "#e2e3e5", "#383d41")
    }
    
    emoji, bg_color, text_color = verdict_colors.get(
        verification_data.verdict, 
        ("❓", "#e2e3e5", "#383d41")
    )
    
    st.markdown(f"""
    <div style="
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: {bg_color};
        color: {text_color};
        margin-bottom: 1rem;
        font-weight: bold;
        font-size: 1.2rem;
    ">
        {emoji} {verification_data.verdict}
    </div>
    """, unsafe_allow_html=True)
    
    # 判别摘要
    st.markdown("**判别摘要：**")
    st.write(verification_data.summary)


# 左边主体
def render_report_tabs(pending_task_id):
    """渲染报告标签页"""
    tab1, tab2 = st.tabs(["📄 AI 分析报告", "📰 新闻原文"])
    
    with tab1:
        # 自定义 CSS：定义一个固定高度、可滚动的容器
        st.markdown("""
            <style>
            .report-container {
                height: 300px;        /* 固定高度 */
                overflow-y: auto;     /* 超出时滚动 */
                border: 1px solid #ddd;
                padding: 1rem;
                border-radius: 8px;
                background-color: #fafafa;
            }
            </style>
        """, unsafe_allow_html=True)

        # 创建可替换的容器
        report_container = st.empty()

        # 初始内容
        with report_container.container():
            st.markdown('<div class="report-container">', unsafe_allow_html=True)
            progress_placeholder = st.empty()  # 在滚动区域内放进度条
            st.markdown('</div>', unsafe_allow_html=True)

        # 等待报告生成完成  
        def report_callback(progress):
            progress_placeholder.progress(progress / 100.0)

        report_data = api_client.wait_for_report(
            pending_task_id,
            poll_interval=1.0,
            progress_callback=report_callback
        )
        

        if report_data:
            with report_container.container():
                st.markdown(f'<div class="report-container">{report_data}</div>', unsafe_allow_html=True)
        else:
            st.error("❌ 报告生成失败")
    
    with tab2:
        # 如果是链接查询，显示原文
        if st.session_state.get("current_query", "").startswith("http"):
            st.components.v1.iframe(
                st.session_state.current_query,
                height=600,
                scrolling=True
            )
        else:
            st.info("💡 点击溯源图中的节点可以查看具体新闻原文")
            st.caption("当前为主题搜索，没有单一原文链接")


# 左下
def render_feedback_section():
    pass


# 右上
def render_timeline_section(timeline_data):
    """渲染时间线"""
    if not timeline_data:
        st.info("暂无时间线数据")
        return
    
    st.subheader("📅 新闻时间线")
    
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
    if not timeline_data.timeline:
        st.info("暂无时间线事件")
        return
    
    for item in timeline_data.timeline:
        with st.expander(f"📅 {item.date} ({item.source_count}篇)", expanded=True):
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


# 右下
def render_external_discussions(discussions):
    """渲染外部讨论链接"""
    st.subheader("💬 社区讨论")
    st.caption("查看其他平台的相关讨论")
    
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



def main():
    """主函数"""
    # 初始化
    init_session_state()
    
    # 获取历史记录并渲染侧边栏
    history = MockAPI.get_user_history()
    render_sidebar(history)
    
    # 检查是否有待处理的任务
    pending_task_id = st.session_state.get('pending_task_id')
    
    if pending_task_id:
        st.title(f"📊 {st.session_state.get('current_query', '正在分析中...')}")
        st.info("正在分析查询内容，各模块将陆续加载...")
        
        # 创建各模块的容器
        report_container = st.empty()
        discussion_container = st.empty()
        
        # 报告模块
        with report_container.container():
            st.subheader("📄 报告生成")
            report_progress = st.progress(0)
            report_status = st.empty()
            
            def report_callback(status, progress):
                status_map = {"pending": "等待中", "running": "生成中", "completed": "完成", "error": "错误"}
                report_status.text(f"{status_map.get(status, status)}... {progress}%")
                report_progress.progress(progress / 100.0)
            
            report_data = api_client.wait_for_report(
                pending_task_id,
                poll_interval=1.0,
                progress_callback=report_callback
            )
            
            if report_data:
                report_status.success("✅ 报告生成完成")
            else:
                report_status.error("❌ 报告生成失败")
        
        # 外部讨论模块
        with discussion_container.container():
            st.subheader("💬 外部讨论")
            discussion_progress = st.progress(0)
            discussion_status = st.empty()
            
            def discussion_callback(status, progress):
                status_map = {"pending": "等待中", "running": "加载中", "completed": "完成", "error": "错误"}
                discussion_status.text(f"{status_map.get(status, status)}... {progress}%")
                discussion_progress.progress(progress / 100.0)
            
            discussions = api_client.wait_for_discussion(
                pending_task_id,
                poll_interval=1.0,
                progress_callback=discussion_callback
            )
            
            if discussions:
                discussion_status.success("✅ 外部讨论加载完成")
            else:
                discussion_status.error("❌ 外部讨论加载失败")
        
        # 保存数据到 session state
        st.session_state.module_report = report_data
        st.session_state.module_discussion = discussions
        
        # 清除待处理任务标记
        del st.session_state.pending_task_id
        
        st.success("🎉 所有模块加载完成！")
        time.sleep(1)
        st.rerun()
        return

    # 页面标题
    st.title(f"📊 {st.session_state.get('current_query', '分析结果')}")
    
    # 左右分栏布局
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        # 真实性判定和判别结果
        render_verdict_section(pending_task_id)

        render_report_tabs(pending_task_id)

        st.divider()

        render_feedback_section()

    with right_col:
        render_timeline_section(pending_task_id)
        
        st.divider()
        # 外部讨论
        render_external_discussions(pending_task_id)
    
    # 底部操作
    st.divider()
    if st.button("← 返回首页"):
        st.switch_page("app.py")


if __name__ == "__main__":
    main()

