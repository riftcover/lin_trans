import os
import subprocess
import sys
import shutil
import glob


def move_compiled_files(target_dir):
    """将编译生成的.pyd文件移动到目标目录"""
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)

    # 查找所有.pyd文件
    pyd_files = glob.glob("*.pyd")

    if not pyd_files:
        print("未找到编译生成的.pyd文件")
        return

    print(f"找到 {len(pyd_files)} 个.pyd文件:")
    for pyd_file in pyd_files:
        print(f"  - {pyd_file}")
        target_path = os.path.join(target_dir, pyd_file)
        try:
            shutil.move(pyd_file, target_path)
            print(f"成功移动 {pyd_file} 到 {target_path}")
        except Exception as e:
            print(f"移动文件 {pyd_file} 时出错: {e}")


def convert_py_to_pyd(script_folder):
    # 确保script文件夹存在
    if not os.path.exists(script_folder):
        print(f"错误: 文件夹 '{script_folder}' 不存在。")
        return
    # path_list = ['agent','app','components','nice_ui','orm','services','tools','utils','vendor','videotrans','api_client']
    path_list = ['utils']
    # 构建Nuitka命令
    for pp in path_list:
        print(f"正在编译模块: {pp}")
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

        try:
            subprocess.run(command, check=True)
            print(f"模块 {pp} 编译成功")
        except subprocess.CalledProcessError as e:
            print(f"编译模块 {pp} 时出错: {e}")
            return False

    print("所有模块编译完成")
    return True


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = r"D:\tool\build3\scripts"

    print("开始编译过程...")
    success = convert_py_to_pyd(current_dir)

    if success:
        print("\n开始移动编译文件...")
        move_compiled_files(target_dir)
        print(f"\n编译和移动过程完成！文件已移动到: {target_dir}")
    else:
        print("\n编译过程中出现错误，跳过文件移动。")
