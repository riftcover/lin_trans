import time

import streamlit as st

# 使用“with”语法添加单选按钮
# with st.sidebar:
#     add_radio = st.radio(
#         "选择一种运输方式",
#         ("标准（5-15天）", "快递（2-5天）")
#     )
# xff = st.sidebar.radio('这是一个选择',(1,2,3))
#
# with st.sidebar:
#
#     xd =st.selectbox(
#         '选择的语言',
#         ('自动','中文','英语','西班牙语','日语')
#     )
#
# with st.sidebar:
#     with st.echo():
#         st.write("这是在侧边栏显示的内容")
with st.sidebar:
    with st.echo():
        "这段代码将在侧边栏中显示。"

    with st.spinner("加载中..."):
        time.sleep(5)
    st.success("完成！")