"""推荐组件"""
import streamlit as st
from typing import List
from models.data_models import Recommendation
from api.mock_api import MockAPI
from api.api_client import api_client
from utils.state import set_current_search


def render_recommendations(recommendations: List[Recommendation]):
    """
    渲染推荐新闻
    
    Args:
        recommendations: 推荐列表
    """
    st.subheader("🔥 热点话题")
    
    # 以卡片形式展示推荐
    cols = st.columns(2)
    
    for idx, rec in enumerate(recommendations):
        with cols[idx % 2]:
            # 计算热度显示
            heat_emoji = "🔥" * int(rec.heat * 5)
            
            with st.container():
                st.markdown(f"""
                <div style="
                    padding: 1rem;
                    border-radius: 0.5rem;
                    background-color: #f0f2f6;
                    margin-bottom: 0.5rem;
                    cursor: pointer;
                ">
                    <div style="font-size: 0.9rem; font-weight: 500;">
                        {rec.title}
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.8rem; color: #666;">
                        热度: {heat_emoji} {rec.heat:.0%}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(
                    "查看详情", 
                    key=f"rec_{idx}",
                    use_container_width=True
                ):
                    # 点击推荐直接搜索
                    with st.spinner("正在加载..."):
                        result = api_client.create_query_task(rec.title)
                        task_id = result.get("task_id")
                        if task_id:
                            set_current_search(rec.title, task_id)
                            st.switch_page("pages/result.py")

