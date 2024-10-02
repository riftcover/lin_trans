import os
import shutil
import subprocess
import sys
import platform
import argparse

# 检查并安装必要的模块
def install_required_modules():
    required_modules = [
        "better_ffmpeg_progress", "colorthief", "darkdetect",
        "httpx", "loguru", "modelscope", "numpy", "openai",
        "packaging", "path", "Pillow", "pydantic", "pydub", "PySide6",
        "scipy", "sqlalchemy", "socksio", "pyinstaller"
    ]

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            print(f"正在安装 {module}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])

# 安装必要的模块
# install_required_modules()

# 清理旧的构建文件
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")

# 添加命令行参数解析
parser = argparse.ArgumentParser(description='构建应用程序')
parser.add_argument('--debug', action='store_true', help='启用调试模式')
args = parser.parse_args()

# 基本的 PyInstaller 打包命令
cmd = [
    "pyinstaller",
    "--name=linlin",
    "--windowed",
    "--onedir",
    "--add-data=models:models",
    "--add-data=orm/linlin.db:orm",
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
]

# 如果是调试模式，添加调试选项
if args.debug:
    cmd.extend(["--debug", "all"])

# 根据操作系统添加特定选项
if platform.system() == "Windows":
    cmd.append("--noconsole")
elif platform.system() == "Darwin":  # macOS
    cmd.extend([
        "--icon=components/assets/linlin.icns",
        "--osx-bundle-identifier=com.yourcompany.yourapp"
    ])

# 添加主文件路径
cmd.append("nice_ui/ui/demo.py")

# 执行打包命令
subprocess.run(cmd, check=True)

print("打包完成!")