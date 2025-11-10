"""推荐组件"""
import streamlit as st
from typing import List
from models.data_models import Recommendation
from api.mock_api import MockAPI
from api.api_client import api_client
from utils.state import set_current_search, reset_result_state
from loguru import logger


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
                    try:
                        # 重置结果页面状态
                        reset_result_state()
                        
                        # 创建查询任务（推荐使用快速模式）
                        with st.spinner("正在创建查询任务..."):
                            task_data = api_client.create_query_task(rec.title, mode="quick")
                            task_id = task_data.get('task_id')
                        
                        if not task_id:
                            st.error("创建查询任务失败")
                            return
                        
                        # 保存查询、任务ID和模式到 session state
                        set_current_search(rec.title, task_id)
                        st.session_state.pending_task_id = task_id
                        st.session_state.query_mode = "quick"
                        
                        # 立即跳转到结果页面
                        st.switch_page("pages/result.py")
                    
                    except Exception as e:
                        st.error(f"创建查询任务失败: {str(e)}")
                        logger.error(f"创建查询任务失败: {str(e)}")

