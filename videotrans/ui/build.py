def convert_encoding(py_file):
    # 将ui生成的ui文件进行Unicode解码
    # 读取生成的 .py 文件并解码 Unicode 字符
    with open(py_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 将 Unicode 字符转换为正常的中文字符
    decoded_content = content.encode('utf-8').decode('unicode_escape')

    # 写回 .py 文件
    with open(py_file, 'w', encoding='utf-8') as f:
        f.write(decoded_content)

if __name__ == "__main__":
    ui_file = 'en.py'  # 替换为你的 .ui 文件名
    convert_encoding(ui_file)
