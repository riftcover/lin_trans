import streamlit as st


st.set_page_config(page_title="分页", page_icon="📈")
st.sidebar.header("分页2")
st.title("字幕处理工具")
# 创建三个列
container = st.container(border=True)
container.write("xd1")

# 字幕翻译
# with col2:
#     st.image("image.png", width=100)  # 替换为你自己的图标路径
#     st.header("字幕翻译")
#     st.write("导入字幕文件，翻译成其他语言")
#
# # 仅导入字幕
# with col3:
#     st.image("image.png", width=100)  # 替换为你自己的图标路径
#     st.header("仅导入字幕")
#     st.write("导入字幕文件，搜索和编辑")
# 运行 Streamlit 应用程序：在终端中运行 `streamlit run your_script.py`


