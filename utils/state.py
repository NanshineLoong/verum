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
    
    # 结果页面相关状态
    if "module_report" not in st.session_state:
        st.session_state.module_report = None
    
    if "module_verification" not in st.session_state:
        st.session_state.module_verification = None
    
    if "module_timeline" not in st.session_state:
        st.session_state.module_timeline = None


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


def reset_result_state():
    """重置结果页面状态（每次创建新查询任务时调用）"""
    st.session_state.module_report = None
    st.session_state.module_verification = None
    st.session_state.module_timeline = None


def set_verification_data(verification):
    """设置判罚数据"""
    st.session_state.module_verification = verification


def set_timeline_data(timeline):
    """设置时间线数据"""
    st.session_state.module_timeline = timeline

