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
    
    if "module_mermaid_timeline" not in st.session_state:
        st.session_state.module_mermaid_timeline = None
    
    # 反馈相关状态
    if "agree_count" not in st.session_state:
        st.session_state.agree_count = 42
    
    if "disagree_count" not in st.session_state:
        st.session_state.disagree_count = 8
    
    if "feedback_given" not in st.session_state:
        st.session_state.feedback_given = False


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
    st.session_state.module_mermaid_timeline = None
    # 重置反馈状态
    reset_feedback_state()


def set_verification_data(verification):
    """设置判罚数据"""
    st.session_state.module_verification = verification


def set_timeline_data(timeline):
    """设置时间线数据"""
    st.session_state.module_timeline = timeline


def set_mermaid_timeline_data(mermaid_timeline):
    """设置 Mermaid Timeline 数据"""
    st.session_state.module_mermaid_timeline = mermaid_timeline


def reset_feedback_state():
    """重置反馈状态"""
    st.session_state.agree_count = 42
    st.session_state.disagree_count = 8
    st.session_state.feedback_given = False


def set_feedback_agree():
    """设置用户点击了'真的！'反馈"""
    st.session_state.agree_count += 1
    st.session_state.feedback_given = True


def set_feedback_disagree():
    """设置用户点击了'假的！'反馈"""
    st.session_state.disagree_count += 1
    st.session_state.feedback_given = True


def get_feedback_state():
    """获取反馈状态"""
    return {
        "agree_count": st.session_state.get("agree_count", 42),
        "disagree_count": st.session_state.get("disagree_count", 8),
        "feedback_given": st.session_state.get("feedback_given", False)
    }

