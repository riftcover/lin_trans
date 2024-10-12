import os
import subprocess
import sys
import shutil

# 清理旧的构建文件
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")

def run_pyinstaller_build():
    # 获取当前脚本的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 主Python文件名
    main_file = "run.py"

    # PyInstaller命令
    pyinstaller_command = [
        "pyinstaller",
        "--name=linlin",
        "--windowed",
        "--onedir",
        "--add-data=nice_ui/language/*.json:nice_ui/language",
        "--hidden-import=scipy",
        "--hidden-import=numpy",
        "--hidden-import=better_ffmpeg_progress",
        "--hidden-import=colorthief",
        "--hidden-import=darkdetect",
        "--hidden-import=httpx",
        "--hidden-import=loguru",
        "--hidden-import=modelscope",
        "--hidden-import=openai",
        "--hidden-import=packaging",
        "--hidden-import=path",
        "--hidden-import=pydantic",
        "--hidden-import=sqlalchemy",
        "--hidden-import=socksio",
        "--add-data=utils:utils",
        main_file
        ]

    print("开始 PyInstaller 构建...")
    # 运行PyInstaller命令
    try:
        subprocess.run(pyinstaller_command, check=True)
        print("PyInstaller 构建成功完成。")
        print(f"可执行文件位于: {os.path.join(script_dir, 'dist', 'linlin')}")
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller 构建失败：{e}")
        sys.exit(1)


if __name__ == "__main__":
    run_pyinstaller_build()