"""债券盘点报告页面"""
import streamlit as st
from pathlib import Path
import base64
import re
from api.mock_api import MockAPI
from components.sidebar import render_sidebar
from utils.state import init_session_state

# 页面配置
st.set_page_config(
    page_title="债券盘点",
    page_icon="📊",
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


@st.cache_data
def load_report_content():
    """加载报告内容"""
    report_path = Path(__file__).parent / "bond" / "全章汇总报告.md"
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception as e:
        st.error(f"读取报告文件失败: {str(e)}")
        return None


def process_images_in_markdown(markdown_text, base_dir):
    """处理 markdown 中的图片路径，转换为 base64 编码的 data URI"""
    # 匹配 markdown 图片语法: ![alt](path)
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    def replace_image(match):
        alt_text = match.group(1)
        image_path = match.group(2)
        
        # 构建完整路径
        full_path = base_dir / image_path
        
        # 检查文件是否存在
        if full_path.exists():
            try:
                # 读取图片并转换为 base64
                with open(full_path, 'rb') as img_file:
                    img_data = img_file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    
                    # 根据文件扩展名确定 MIME 类型
                    ext = full_path.suffix.lower()
                    mime_types = {
                        '.png': 'image/png',
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.gif': 'image/gif',
                        '.svg': 'image/svg+xml',
                        '.webp': 'image/webp'
                    }
                    mime_type = mime_types.get(ext, 'image/png')
                    
                    # 返回 data URI 格式的图片
                    return f'![{alt_text}](data:{mime_type};base64,{img_base64})'
            except Exception:
                # 如果加载失败，返回原始内容，不显示警告
                return match.group(0)
        else:
            # 如果文件不存在，返回原始内容，不显示警告
            return match.group(0)
    
    return re.sub(pattern, replace_image, markdown_text)


def main():
    """主函数"""
    # 初始化
    init_session_state()
    
    # 获取历史记录并渲染侧边栏
    history = MockAPI.get_user_history()
    render_sidebar(history)
    
    # 返回首页按钮
    if st.button("← 返回首页"):
        st.switch_page("app.py")
    
    # 页面标题
    st.title("📊 债券盘点报告")
    
    # 加载报告内容
    report_text = load_report_content()
    
    if report_text:
        # 处理图片路径，将相对路径转换为 base64 data URI
        bond_dir = Path(__file__).parent / "bond"
        processed_text = process_images_in_markdown(report_text, bond_dir)
        
        # 使用 Streamlit 的 markdown 渲染，它原生支持表格和图片
        st.markdown("""
        <style>
            .report-content table {
                border-collapse: collapse;
                width: 100%;
                margin: 1rem 0;
            }
            .report-content table th,
            .report-content table td {
                border: 1px solid #ddd;
                padding: 0.5rem;
                text-align: left;
            }
            .report-content table th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            /* 图片样式 - 确保适配页面 */
            .report-content img,
            .report-content p img,
            div[data-testid="stMarkdownContainer"] img {
                max-width: 100% !important;
                width: auto !important;
                height: auto !important;
                display: block !important;
                margin: 1rem auto !important;
                object-fit: contain;
            }
            /* 限制图片最大宽度，避免过大 */
            .report-content img {
                max-width: min(100%, 800px) !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # 直接渲染 markdown，不限制高度
        st.markdown('<div class="report-content">', unsafe_allow_html=True)
        st.markdown(processed_text)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.error("❌ 无法加载报告文件，请确保文件存在")


if __name__ == "__main__":
    main()

