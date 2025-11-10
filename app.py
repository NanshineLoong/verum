"""Verum - 新闻溯源系统主页"""
import streamlit as st
from api.mock_api import MockAPI
from components.sidebar import render_sidebar
from components.search_box import render_search_box
from components.recommendations import render_recommendations
from utils.state import init_session_state


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


def main():
    """主函数"""
    # 初始化session state
    init_session_state()
    
    # 获取数据
    history = MockAPI.get_user_history()
    recommendations = MockAPI.get_recommendations()
    
    # 渲染侧边栏
    render_sidebar(history)
    
    # 主内容区
    # 搜索框
    render_search_box()
    
    st.divider()
    
    # 推荐新闻
    render_recommendations(recommendations)


if __name__ == "__main__":
    main()

