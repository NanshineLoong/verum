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

    # 思考模式选择（可选，默认浅模式）
    mode_deep = st.checkbox(
        "🧠 深度溯源",
        value=False,
        help="更全面的分析，耗时较长"
    )
    
    # 将选择转换为模式值
    mode = "deep" if mode_deep else "quick"
    
    # 处理搜索
    if search_clicked and query:
        try:
            # 重置结果页面状态
            reset_result_state()
            
            # 创建查询任务
            with st.spinner(f"正在创建查询任务（{'深度' if mode == 'deep' else '浅度'}思考模式）..."):
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

