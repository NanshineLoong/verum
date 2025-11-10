"""结果展示页面"""
import streamlit as st
from api.mock_api import MockAPI
from api.api_client import api_client
from components.sidebar import render_sidebar
from utils.state import (
    init_session_state,
    set_verification_data,
    set_timeline_data,
    set_mermaid_timeline_data
)
from loguru import logger

# 使用 MockAPI 而不是真实的 API 客户端
# api_client = MockAPI()



# 页面配置
st.set_page_config(
    page_title="Verum",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 隐藏 Streamlit 页面导航器
st.markdown("""
<style>
    /* 隐藏页面导航器 */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* 或者使用更通用的选择器 */
    section[data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* 隐藏页面导航器的容器 */
    div[data-testid="stSidebarNav"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)


def render_verdict_section(verification):
    """渲染真实性判定结果"""

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
        padding: 0.5rem;
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
    
    # 判别摘要（折叠显示）
    with st.expander("📋 查看判别摘要", expanded=False):
        st.caption(verification.summary)


def render_report_tabs(report_text, current_query):
    """渲染报告标签页"""

    tab1, tab2 = st.tabs(["📰 新闻原文", "📄 AI 分析报告"])
    
    with tab1:
        # 如果是链接查询，显示原文
        if current_query.startswith("http"):
            # 先尝试预览
            st.components.v1.iframe(current_query, height=400, scrolling=True)
            
            # 在下方直接显示链接
            st.markdown(f"""
            <div style="margin-top: 1rem; padding: 1rem; background-color: #f8f9fa; border-radius: 0.5rem;">
                <a href="{current_query}" target="_blank" style="
                    display: inline-block;
                    padding: 0.5rem 1rem;
                    background-color: #1f77b4;
                    color: white;
                    text-decoration: none;
                    border-radius: 0.25rem;
                    font-weight: 500;
                ">🔗 在新标签页打开原文</a>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("💡 当前为主题搜索，没有单一原文链接")
            st.caption("您可以在时间线模块中查看相关新闻来源")
            st.markdown('<div class="report-container">', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        if report_text:
            import markdown
            html_text = markdown.markdown(report_text)
            st.markdown(f"""
            <div style="
                height: 400px;
                overflow-y: auto;
                padding: 1rem;
                border: 1px solid #e0e0e0;
                border-radius: 0.5rem;
                background-color: #ffffff;
            ">
            {html_text}
            </div>
            """, unsafe_allow_html=True)

        else:
            st.info("⏳ 报告生成中，请稍候...")


def render_feedback_section():
    """渲染反馈按钮"""
    st.markdown("### 💭 Verum 是否准确？")
    
    col1, col2 = st.columns(2)
    
    # 初始化计数器和反馈状态
    if 'agree_count' not in st.session_state:
        st.session_state.agree_count = 42
    if 'disagree_count' not in st.session_state:
        st.session_state.disagree_count = 8
    if 'feedback_given' not in st.session_state:
        st.session_state.feedback_given = False
    
    with col1:
        if st.button(
            f"真的！ ({st.session_state.agree_count})", 
            use_container_width=True,
            disabled=st.session_state.feedback_given
        ):
            st.session_state.agree_count += 1
            st.session_state.feedback_given = True
            st.rerun()
    
    with col2:
        if st.button(
            f"假的! ({st.session_state.disagree_count})", 
            use_container_width=True,
            disabled=st.session_state.feedback_given
        ):
            st.session_state.disagree_count += 1
            st.session_state.feedback_given = True
            st.rerun()
    
    # 显示感谢提示
    if st.session_state.feedback_given:
        st.success("✅ 感谢您的反馈！")


def render_timeline_mermaid(timeline_mermaid_data):
    """渲染 Mermaid Timeline 图表"""
    st.subheader("新闻脉络")
    st.caption("查看新闻的来龙去脉")
    
    if not timeline_mermaid_data:
        st.info("⏳ 正在生成时间线图表...")
        return
    
    # 使用 iframe 来渲染 Mermaid，确保 JavaScript 可以正常执行
    # 创建完整的 HTML 文档，包含缩放功能
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                background-color: #ffffff;
                overflow: hidden;
            }}
            #zoom-container {{
                position: relative;
                width: 100%;
                height: 100vh;
                overflow: auto;
                background-color: #f8f9fa;
            }}
            #mermaid-wrapper {{
                transform-origin: top left;
                transition: transform 0.3s ease;
                padding: 0.5rem;
                min-width: fit-content;
                min-height: fit-content;
            }}
            .mermaid {{
                text-align: center;
                background-color: #ffffff;
                padding: 0.5rem;
                border-radius: 0.25rem;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            #zoom-controls {{
                position: fixed;
                top: 5px;
                right: 5px;
                z-index: 1000;
                background-color: rgba(255, 255, 255, 0.9);
                padding: 0.25rem;
                border-radius: 0.25rem;
                box-shadow: 0 1px 4px rgba(0,0,0,0.15);
            }}
            .zoom-btn {{
                padding: 0.25rem 0.5rem;
                border: 1px solid #ddd;
                border-radius: 0.25rem;
                background-color: #ffffff;
                cursor: pointer;
                font-size: 0.75rem;
                user-select: none;
            }}
            .zoom-btn:hover {{
                background-color: #f0f0f0;
            }}
            .zoom-btn:active {{
                background-color: #e0e0e0;
            }}
        </style>
    </head>
    <body>
        <div id="zoom-controls">
            <button class="zoom-btn" onclick="resetZoom()" title="重置缩放 (Ctrl+滚轮缩放)">重置</button>
        </div>
        <div id="zoom-container">
            <div id="mermaid-wrapper">
                <div class="mermaid">
{timeline_mermaid_data}
                </div>
            </div>
        </div>
        <script>
            let currentZoom = 1.0;
            const minZoom = 0.5;
            const maxZoom = 3.0;
            const zoomStep = 0.1;
            
            const wrapper = document.getElementById('mermaid-wrapper');
            
            function updateZoom() {{
                wrapper.style.transform = `scale(${{currentZoom}})`;
            }}
            
            function zoomIn() {{
                if (currentZoom < maxZoom) {{
                    currentZoom = Math.min(currentZoom + zoomStep, maxZoom);
                    updateZoom();
                }}
            }}
            
            function zoomOut() {{
                if (currentZoom > minZoom) {{
                    currentZoom = Math.max(currentZoom - zoomStep, minZoom);
                    updateZoom();
                }}
            }}
            
            function resetZoom() {{
                currentZoom = 1.0;
                updateZoom();
            }}
            
            // 初始化 Mermaid
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'default',
                flowchart: {{ useMaxWidth: true }},
                timeline: {{ useMaxWidth: true }}
            }});
            
            // 支持鼠标滚轮缩放（按住 Ctrl 键）
            document.addEventListener('wheel', function(e) {{
                if (e.ctrlKey) {{
                    e.preventDefault();
                    if (e.deltaY < 0) {{
                        zoomIn();
                    }} else {{
                        zoomOut();
                    }}
                }}
            }}, {{ passive: false }});
        </script>
    </body>
    </html>
    """
    
    # 使用 components.v1.html 创建 iframe
    st.components.v1.html(html_content, height=200, scrolling=False)

def render_reference_section(timeline_data):
    """渲染参考新闻"""
    
    st.subheader("相关新闻")
    st.caption("查看相关新闻来源")
    
    if not timeline_data:
        st.info("⏳ 正在搜索新闻...")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # 参考新闻内容
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
    else:
        st.info("暂无时间线事件")


def render_external_discussions():
    """渲染外部讨论链接"""
    st.subheader("社区讨论")
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

    # 页面标题 - 使用大喇叭图标并限制长度
    display_query = current_query if len(current_query) <= 30 else current_query[:25] + "..."
    st.title(f"📢 {display_query}")
    
    # 获取当前已加载的数据
    report_text = st.session_state.get('module_report')
    verification = st.session_state.get('module_verification')
    timeline_data = st.session_state.get('module_timeline')
    mermaid_timeline_data = st.session_state.get('module_mermaid_timeline')
    
    # === 第一步：先创建可替换的占位容器并渲染当前内容 ===

    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        verdict_placeholder = st.empty()
        with verdict_placeholder.container():
            render_verdict_section(verification)
                
        report_placeholder = st.empty()
        with report_placeholder.container():
            render_report_tabs(report_text, current_query)
        
        render_feedback_section()
    
    with right_col:
        # Mermaid Timeline 在最上面
        mermaid_placeholder = st.empty()
        with mermaid_placeholder.container():
            render_timeline_mermaid(mermaid_timeline_data)
                
        timeline_placeholder = st.empty()
        with timeline_placeholder.container():
            render_reference_section(timeline_data)
                
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
                render_reference_section(timeline_data)
        except Exception as e:
            logger.error(f"生成时间线失败: {str(e)}")
            with timeline_placeholder.container():
                st.markdown('<div class="timeline-container">❌ 时间线生成失败，请稍后重试</div>', unsafe_allow_html=True)
    
    # 加载 Mermaid Timeline（如果报告已加载但 Mermaid Timeline 还没加载）
    if task_id and report_text and not mermaid_timeline_data:
        try:
            logger.info(f"开始生成 Mermaid Timeline: {task_id}")
            mermaid_timeline_data = api_client.create_mermaid_timeline(task_id=task_id)
            set_mermaid_timeline_data(mermaid_timeline_data)
            logger.info("Mermaid Timeline 生成完成")
            with mermaid_placeholder.container():
                render_timeline_mermaid(mermaid_timeline_data)
        except Exception as e:
            logger.error(f"生成 Mermaid Timeline 失败: {str(e)}")
            with mermaid_placeholder.container():
                st.error(f"❌ Mermaid Timeline 生成失败: {str(e)}")


if __name__ == "__main__":
    main()
