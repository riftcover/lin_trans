import base64

import streamlit as st

# 设置页面标题
st.title("字幕处理工具")

# 自定义CSS样式
st.markdown("""
    <style>
    .card {
        border: 1px solid #d9d9d9;
        border-radius: 10px;
        padding: 20px;
        margin: 10px;
        text-align: center;
        box-shadow: 2px 2px 12px rgba(0, 0, 0, 0.1);
    }
    .card img {
        width: 50px;
        margin-bottom: 10px;
    }
    .card h3 {
        margin: 0;
        color: #1890ff;
    }
    .card p {
        color: #666;
    }
    </style>
    """, unsafe_allow_html=True)

# 创建卡片
def create_card(image_path, title, description):
    card_content = f"""
    <div class="card">
        <img src="data:image/png;base64,{image_path}">
        <h3>{title}</h3>
        <p>{description}</p>
    </div>
    """
    return card_content

# 读取并编码图像
def load_image_as_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return encoded_string

# 图像路径（确保路径正确）
image_path = "../assets/image/t2.png"
image_base64 = load_image_as_base64(image_path)

# 创建三个列
col1, col2, col3 = st.columns(3)

# 在每个列中显示卡片
with col1:
    st.markdown(create_card(image_base64, "音视频转字幕", "导入音频或视频，自动生成字幕"), unsafe_allow_html=True)

with col2:
    st.markdown(create_card(image_base64, "字幕翻译", "导入字幕文件，翻译成其他语言"), unsafe_allow_html=True)

with col3:
    st.markdown(create_card(image_base64, "仅导入字幕", "导入字幕文件，搜索和编辑"), unsafe_allow_html=True)
