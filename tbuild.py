import os
import subprocess
import sys

def convert_py_to_pyd(script_folder):
    # 确保script文件夹存在
    if not os.path.exists(script_folder):
        print(f"错误: 文件夹 '{script_folder}' 不存在。")
        return
    # path_list = ['agent','app','components','nice_ui','orm','tools','utils','vendor','videotrans']
    path_list = ['api_client']
    # 构建Nuitka命令
    for pp in path_list:
        if pp == 'api_client':
            # 对于单独的 Python 文件，使用不同的命令
            command = [
                sys.executable, '-m', 'nuitka',
                '--python-flag=no_warnings,-O,no_docstrings',
                '--remove-output',
                '--no-pyi-file',
                '--module', 'api_client.py',
            ]
        else:
            command = [
                sys.executable, '-m', 'nuitka',
                '--python-flag=no_warnings,-O,no_docstrings',
                '--remove-output',
                '--no-pyi-file',
                '--module', pp,
                f'--include-package={pp}',
            ]

        subprocess.run(command, check=True)

    # command = [
    # sys.executable, '-m', 'nuitka',
    # # '--python-flag=no_warnings,-O,no_docstrings',
    # '--remove-output',
    # # '--no-pyi-file',
    # '--module','nice_ui',
    # # '--enable-plugin=pyside6',
    # '--include-package=nice_ui',
    #
    #     ]

    subprocess.run(command, check=True)


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    convert_py_to_pyd(current_dir)
