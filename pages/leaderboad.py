import streamlit as st
import json
from collections import defaultdict
from pathlib import Path
from datetime import datetime
import re
from api.mock_api import MockAPI
from components.sidebar import render_sidebar
from utils.state import init_session_state

# 设置页面配置
st.set_page_config(
    page_title="热榜聚合", 
    page_icon="🔥", 
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

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    .time-badge {
        background: rgba(255,255,255,0.2);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin-top: 0.5rem;
    }
    .platform-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        transition: transform 0.2s;
    }
    .rank-badge {
        display: inline-block;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        text-align: center;
        line-height: 40px;
        font-weight: bold;
        color: white;
        margin-right: 1rem;
    }
    .rank-1 { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .rank-2 { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .rank-3 { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .rank-other { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .news-title {
        font-size: 1.1rem;
        font-weight: 500;
        color: #333;
        margin-bottom: 0.5rem;
    }
    .news-link {
        color: #667eea;
        text-decoration: none;
        font-size: 0.9rem;
    }
    .news-link:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# 读取 JSONL 文件
@st.cache_data
def load_data(file_path):
    platforms = defaultdict(list)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                item = json.loads(line.strip())
                # 使用 source 字段作为平台名称
                platform = item.get('source', 'unknown')
                platforms[platform].append(item)
    
    # 对每个平台的数据按 rank 排序，并限制数量
    for platform in platforms:
        platforms[platform] = sorted(platforms[platform], key=lambda x: x.get('rank', 999))[:20]  # 只显示前20条
    
    return dict(platforms)

# 平台名称映射
PLATFORM_NAMES = {
    'weibo': '微博热搜',
    'zhihu': '知乎热榜',
    'bilibili-hot-search': 'B站热搜',
    'toutiao': '今日头条',
    'douyin': '抖音热榜',
    'github-trending-today': 'GitHub趋势',
    'coolapk': '酷安热榜',
    'tieba': '百度贴吧',
    'wallstreetcn': '华尔街见闻',
    'thepaper': '澎湃新闻',
    'cls-hot': '财联社',
    'xueqiu': '雪球热榜',
    'unknown': '未知平台'
}

# 平台颜色映射
PLATFORM_COLORS = {
    'weibo': '#ff6b6b',
    'zhihu': '#4ecdc4',
    'bilibili-hot-search': '#00a1d6',
    'toutiao': '#ff6600',
    'douyin': '#000000',
    'github-trending-today': '#24292e',
    'coolapk': '#00d4aa',
    'tieba': '#3385ff',
    'wallstreetcn': '#1a1a1a',
    'thepaper': '#d32f2f',
    'cls-hot': '#ff5722',
    'xueqiu': '#1e88e5',
}

def get_platform_display_name(platform_key):
    return PLATFORM_NAMES.get(platform_key, platform_key.upper())

def get_platform_color(platform_key):
    return PLATFORM_COLORS.get(platform_key, '#667eea')

def find_jsonl_files():
    """查找同级目录下的所有jsonl文件"""
    current_dir = Path(__file__).parent
    jsonl_files = list(current_dir.glob("*.jsonl"))
    # 按修改时间排序，最新的在前
    jsonl_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return jsonl_files

def extract_time_from_filename(filename):
    """从文件名提取时间信息"""
    # 格式: news_YYYYMMDD_HHMMSS.jsonl
    match = re.search(r'news_(\d{8})_(\d{6})', filename)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        try:
            dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
            return dt.strftime("%Y年%m月%d日 %H:%M:%S")
        except:
            pass
    return None

# 主函数
def main():
    """主函数"""
    # 初始化session state
    init_session_state()
    
    # 获取历史记录并渲染侧边栏
    history = MockAPI.get_user_history()
    render_sidebar(history)
    
    # 返回首页按钮
    if st.button("← 返回首页"):
        st.switch_page("app.py")
    
    # 页面头部
    st.markdown("""
    <div class="main-header">
        <h1>🔥 全网热榜聚合</h1>
        <p style="font-size: 1.2rem; margin-top: 0.5rem;">一站式浏览各大平台热门内容</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 自动查找jsonl文件，直接使用第一个
    jsonl_files = find_jsonl_files()
    
    if not jsonl_files:
        st.warning("⚠️ 未找到JSONL文件，请确保同级目录下有 .jsonl 文件")
        return
    
    # 自动选择第一个文件（最新的）
    selected_file = jsonl_files[0]
    
    # 提取时间信息
    time_str = extract_time_from_filename(selected_file.name)
    current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    
    try:
        # 加载数据
        platforms_data = load_data(str(selected_file))
        
        if not platforms_data:
            st.warning("⚠️ 文件中没有有效数据")
            return
        
        # 按平台名称排序
        platform_keys = sorted(platforms_data.keys(), key=lambda x: get_platform_display_name(x))
        
        # 主内容区域 - 控制面板
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            # 平台选择下拉框
            selected_platform = st.selectbox(
                "📱 选择平台",
                options=platform_keys,
                format_func=get_platform_display_name,
                index=0,
                key="platform_selector"
            )
        
        with col2:
            # 总条目数
            total_items = sum(len(items) for items in platforms_data.values())
            st.metric("总条目数", total_items)
        
        with col3:
            # 平台数量
            st.metric("平台数量", len(platforms_data))
        
        with col4:
            # 当前平台条目数
            current_count = len(platforms_data[selected_platform])
            st.metric("当前条目", current_count)
        
        # 时间信息
        col1, col2 = st.columns([3, 1])
        with col1:
            if time_str:
                st.info(f"📅 **数据时间**: {time_str} | 🕐 **当前时间**: {current_time}")
            else:
                st.info(f"📅 **数据时间**: 今天 | 🕐 **当前时间**: {current_time}")
        
        st.markdown("---")
        
        # 各平台条目统计（可折叠）
        with st.expander("📋 查看各平台条目统计", expanded=False):
            cols = st.columns(4)
            for idx, platform in enumerate(platform_keys):
                count = len(platforms_data[platform])
                platform_name = get_platform_display_name(platform)
                with cols[idx % 4]:
                    if platform == selected_platform:
                        st.markdown(f"**🟢 {platform_name}**")
                        st.markdown(f"**{count} 条**")
                    else:
                        st.markdown(f"⚪ {platform_name}")
                        st.markdown(f"{count} 条")
        
        st.markdown("---")
        
        # 显示选中平台的热榜内容
        if selected_platform:
            display_name = get_platform_display_name(selected_platform)
            platform_color = get_platform_color(selected_platform)
            
            # 平台标题
            st.markdown(f"""
            <div style="background: {platform_color}; padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem;">
                <h2 style="color: white; margin: 0;">📌 {display_name} 热榜</h2>
            </div>
            """, unsafe_allow_html=True)
            
            items = platforms_data[selected_platform]
            
            # 显示热榜内容（只显示前20条）
            for idx, item in enumerate(items):
                rank = item.get('rank', idx + 1)
                title = item.get('title', '无标题')
                url = item.get('url', '#')
                
                # 排名徽章样式
                if rank == 1:
                    rank_class = "rank-1"
                    rank_emoji = "🥇"
                elif rank == 2:
                    rank_class = "rank-2"
                    rank_emoji = "🥈"
                elif rank == 3:
                    rank_class = "rank-3"
                    rank_emoji = "🥉"
                else:
                    rank_class = "rank-other"
                    rank_emoji = ""
                
                # 卡片布局
                st.markdown(f"""
                <div class="platform-card">
                    <div style="display: flex; align-items: center;">
                        <span class="rank-badge {rank_class}">{rank_emoji if rank_emoji else rank}</span>
                        <div style="flex: 1;">
                            <div class="news-title">{title}</div>
                            <a href="{url}" target="_blank" class="news-link">🔗 查看详情 →</a>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"❌ 读取文件出错: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()
