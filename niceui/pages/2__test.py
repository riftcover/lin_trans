import streamlit as st

# 使用对象表示法添加选择框
add_selectbox = st.sidebar.selectbox(
    "您希望如何联系您？",
    ("电子邮件", "家庭电话", "移动电话")
)

# 使用“with”语法添加单选按钮
with st.sidebar:
    add_radio = st.radio(
        "选择一种运输方式",
        ("标准（5-15天）", "快递（2-5天）")
    )
xff = st.sidebar.radio('这是一个选择',(1,2,3))

with st.sidebar:
    xd =st.selectbox(
        '选择的语言',
        ('自动','中文','英语','西班牙语','日语')
    )