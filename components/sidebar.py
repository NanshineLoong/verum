"""侧边栏组件"""
import streamlit as st
from typing import List
from models.data_models import HistoryItem
from utils.state import clear_search


def render_sidebar(history: List[HistoryItem]):
    """
    渲染侧边栏
    
    Args:
        history: 历史记录列表
    """
    with st.sidebar:
        st.title("🔍 Verum")
        
        # 新对话按钮
        if st.button("➕ 新对话", use_container_width=True):
            clear_search()
            st.rerun()
        
        st.divider()
        
        # 历史记录
        st.subheader("📚 历史记录")
        
        if history:
            for item in history:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(
                            item.query, 
                            key=f"history_{item.timestamp}",
                            use_container_width=True
                        ):
                            st.session_state.current_query = item.query
                            st.rerun()
                    with col2:
                        st.caption(item.timestamp[-5:])  # 显示月-日
        else:
            st.info("暂无历史记录")

