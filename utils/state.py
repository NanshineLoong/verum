"""Session State 管理工具"""
import streamlit as st
from typing import Optional


def init_session_state():
    """初始化session state"""
    if "current_graph_id" not in st.session_state:
        st.session_state.current_graph_id = None
    
    if "current_query" not in st.session_state:
        st.session_state.current_query = ""
    
    if "search_result" not in st.session_state:
        st.session_state.search_result = None
    
    if "selected_node" not in st.session_state:
        st.session_state.selected_node = None


def set_current_search(query: str, graph_id: str):
    """设置当前搜索结果"""
    st.session_state.current_query = query
    st.session_state.current_graph_id = graph_id


def get_current_graph_id() -> Optional[str]:
    """获取当前的graph_id"""
    return st.session_state.get("current_graph_id")


def clear_search():
    """清除搜索结果"""
    st.session_state.current_graph_id = None
    st.session_state.current_query = ""
    st.session_state.search_result = None

