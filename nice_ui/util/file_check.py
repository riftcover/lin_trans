import re


def is_valid_srt_content(file_content):
    """
    检查文件内容是否符合 .srt 文件的格式。

    :param file_content: 文件内容（字符串）
    :return: 如果内容符合 .srt 格式，返回 True；否则返回 False
    """
    file_extension = file_path.split(".")[-1].lower()

    # 检查扩展名是否为 'srt'
    if file_extension == "srt":
        # 将文件内容按行分割
        lines = file_content.strip().split("\n")

        # 用于匹配时间戳的正则表达式
        timestamp_pattern = re.compile(
            r"^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$"
        )

        # 用于匹配序号的正则表达式
        index_pattern = re.compile(r"^\d+$")

        # 用于匹配空行的正则表达式
        empty_line_pattern = re.compile(r"^\s*$")

        # 初始化状态变量
        expecting_index = True
        expecting_timestamp = False
        expecting_subtitle_text = False

        for line in lines:
            line = line.strip()

            if expecting_index:
                if index_pattern.match(line):
                    expecting_index = False
                    expecting_timestamp = True
                else:
                    return False

            elif expecting_timestamp:
                if timestamp_pattern.match(line):
                    expecting_timestamp = False
                    expecting_subtitle_text = True
                else:
                    return False

            elif expecting_subtitle_text:
                if empty_line_pattern.match(line):
                    expecting_subtitle_text = False
                    expecting_index = True
                elif not line:
                    return False

            else:
                return False

        return True
    else:
        return False


def is_valid_srt_file(file_path):
    """
    检查文件是否是有效的 .srt 文件。

    :param file_path: 文件的路径
    :return: 如果是有效的 .srt 文件，返回 True；否则返回 False
    """

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            file_content = file.read()
            return is_valid_srt_content(file_content)
    except Exception as e:
        print(f"Error reading file: {e}")
        return False


if __name__ == "__main__":
    file_path = "/Users/locodol/Movies/2set.srt"
    if is_valid_srt_file(file_path):
        print(f"{file_path} 是一个有效的 .srt 文件。")
    else:
        print(f"{file_path} 不是")
