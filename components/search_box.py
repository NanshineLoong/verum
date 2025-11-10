"""搜索框组件"""
import streamlit as st
from api.mock_api import MockAPI
from api.api_client import api_client
from utils.state import set_current_search, reset_result_state
from loguru import logger

# api_client = MockAPI()

def render_search_box():
    """渲染搜索框"""
    # Logo 和标题
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>Verum</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>真相，触手可及</p>", unsafe_allow_html=True)
    
    # 搜索框
    col1, col2 = st.columns([5, 1])
    
    with col1:
        query = st.text_input(
            "搜索",
            placeholder="输入新闻主题或粘贴新闻链接，开始溯源分析",
            label_visibility="collapsed",
            key="search_input"
        )
    
    with col2:
        search_clicked = st.button("搜索", use_container_width=True)

    # 思考模式选择（下拉选择，默认自动）
    mode_options = {
        "自动": "auto",
        "深度溯源": "deep",
        "快速查找": "quick"
    }
    col1, _ = st.columns([1, 7])

    with col1:
        mode_label = st.selectbox(
            "思考模式",
            options=list(mode_options.keys()),
            index=0,  # 默认选择"自动"
            help="自动：根据查询内容智能选择模式；深度溯源：更全面的分析，耗时较长；快速查找：快速检索事实信息"
        )
    
    # 将选择转换为模式值
    mode = mode_options[mode_label]
    
    # 处理搜索
    if search_clicked and query:
        try:
            # 重置结果页面状态
            reset_result_state()
            
            # 创建查询任务
            mode_display = {
                "auto": "自动",
                "deep": "深度",
                "quick": "快速"
            }.get(mode, "自动")
            with st.spinner(f"正在创建查询任务（{mode_display}模式）..."):
                task_data = api_client.create_query_task(query, mode)
                task_id = task_data.get('task_id')
            
            if not task_id:
                st.error("创建查询任务失败")
                return query
            
            # 保存查询、任务ID和模式到 session state
            set_current_search(query, task_id)
            st.session_state.pending_task_id = task_id
            st.session_state.query_mode = mode
            
            # 立即跳转到结果页面
            st.switch_page("pages/result.py")
        
        except Exception as e:
            st.error(f"创建查询任务失败: {str(e)}")
            logger.error(f"创建查询任务失败: {str(e)}")
    
    return query

