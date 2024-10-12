import os
import shutil
import subprocess
import sys
import platform
import argparse
import site
import time

# 检查并安装必要的模块
def install_required_modules():
    required_modules = [
        "better_ffmpeg_progress", "colorthief", "darkdetect",
        "httpx", "loguru", "modelscope", "numpy", "openai",
        "packaging", "path", "Pillow", "pydantic", "pydub", "PySide6",
        "scipy", "sqlalchemy", "zhipuai", "socksio"
    ]

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            print(f"正在安装 {module}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])

# 添加命令行参数解析
parser = argparse.ArgumentParser(description='构建应用程序')
parser.add_argument('--debug', action='store_true', help='启用调试模式')
args = parser.parse_args()


# 定义版本号
your_version = "0.1.0"  # 替换为您的实际版本号

# 定义项目根目录和models目录
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
MODELS_DIR = os.path.join(PROJECT_ROOT, 'models')
RESULT_DIR = os.path.join(PROJECT_ROOT, 'result')
NICE_UI_DIR = os.path.join(PROJECT_ROOT, 'nice_ui')
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
ORM_DIR = os.path.join(PROJECT_ROOT, 'orm')


# 确保必要的目录存在
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"创建目录: {directory}")

# 创建 result 和 logs 目录
ensure_dir(RESULT_DIR)
ensure_dir(LOGS_DIR)
# 基本的 Nuitka 打包命令
cmd = [
    sys.executable,
    "-m", "nuitka",
    "--standalone",
    "--remove-output",
    "--nofollow-imports",
    "--enable-plugin=pyside6",
    "--plugin-enable=numpy,torch",
    # "--include-qt-plugins=translations",
    # "--include-package=scipy",
    # # "--include-package=numpy",
    # "--include-package=better_ffmpeg_progress",
    # "--include-package=colorthief",
    # "--include-package=darkdetect",
    # "--include-package=httpx",
    # "--include-package=loguru",
    # "--include-package=modelscope",
    # "--include-package=openai",
    # "--include-package=packaging",
    # "--include-package=path",
    # "--include-package=pydantic",
    # "--include-package=sqlalchemy",
    # "--include-package=socksio",
    "--output-dir=build",
    f"--windows-product-version={your_version}",
    f"--windows-file-version={your_version}",
    "--include-data-dir=models=models",  # 包含models文件夹
    "--include-data-files=orm/linlin.db=orm/linlin.db",  # 包含linlin.db文件
    "--include-data-dir=nice_ui/language=nice_ui/language",  # 包含linlin.db文件
    "--include-data-dir=logs=logs",  # 包含logs文件夹
    "--include-data-dir=result=result",  # 包含logs文件夹
]

if args.debug:
    cmd.extend([
        "--debug",
        "--verbose",
        "--show-memory",
        "--show-progress",
    ])

# 如果是 macOS，移除 app bundle 创建（为了更容易调试）
if platform.system() == "Darwin":
    cmd = [opt for opt in cmd if opt != "--macos-create-app-bundle"]

# 根据操作系统添加特定选项
if platform.system() == "Windows":
    cmd.extend([
        # "--windows-disable-console",
        "--windows-icon-from-ico=components/assets/linlin.ico",  # 添加 Windows 图标
    ])
elif platform.system() == "Darwin":  # macOS
    if not args.debug:
        cmd.extend([
            "--macos-create-app-bundle",
            "--macos-app-icon=components/assets/linlin.icns",
        ])
    # 检测 Mac 芯片类型并设置目标架构
    if platform.machine() == "arm64":
        cmd.append("--macos-target-arch=arm64")
    else:
        cmd.append("--macos-target-arch=x86_64")

# 添加主文件路径
cmd.append("run.py")


# 复制 models 文件夹到打包目录
# if platform.system() == "Darwin":  # macOS
#     app_name = "run.app"  # 替换为您的应用程序名称
#     models_src = "models"
#     models_dst = os.path.join("build", app_name, "Contents", "Resources", "models")
#     if os.path.exists(models_src):
#         shutil.copytree(models_src, models_dst, dirs_exist_ok=True)
#
#     # 确保 orm 目录存在，并复制 linlin.db
#     orm_dir = os.path.join("build", app_name, "Contents", "Resources", "orm")
#     os.makedirs(orm_dir, exist_ok=True)
#     linlin_db_src = "orm/linlin.db"
#     linlin_db_dst = os.path.join(orm_dir, "linlin.db")
#     if os.path.exists(linlin_db_src):
#         shutil.copy2(linlin_db_src, linlin_db_dst)
# else:
#     models_src = "models"
#     models_dst = os.path.join("build", "models")
#     if os.path.exists(models_src):
#         shutil.copytree(models_src, models_dst, dirs_exist_ok=True)
#
#     # 确保 orm 目录存在，并复制 linlin.db
#     orm_dir = os.path.join("build", "orm")
#     os.makedirs(orm_dir, exist_ok=True)
#     linlin_db_src = "orm/linlin.db"
#     linlin_db_dst = os.path.join(orm_dir, "linlin.db")
#     if os.path.exists(linlin_db_src):
#         shutil.copy2(linlin_db_src, linlin_db_dst)


# 在打包完成后，复制 modelscope 库
def copy_modelscope():
    # 获取 modelscope 库的路径
    modelscope_path = None
    for path in site.getsitepackages():
        possible_path = os.path.join(path, 'modelscope')
        if os.path.exists(possible_path):
            modelscope_path = possible_path
            break

    if not modelscope_path:
        print("无法找到 modelscope 库路径")
        return

    # 确定目标路径
    if platform.system() == "Darwin":  # macOS
        app_name = "run.app"  # 替换为您的应用程序名称
        dst_path = os.path.join("build", app_name, "Contents", "MacOS", "modelscope")
    else:  # Windows 或其他系统
        dst_path = os.path.join("build", "modelscope")

    # 复制 modelscope 库
    print(f"正在复制 modelscope 库从 {modelscope_path} 到 {dst_path}")
    shutil.copytree(modelscope_path, dst_path, dirs_exist_ok=True)

start_time = time.time()
# 在打包完成后调用复制函数
# 安装必要的模块
# install_required_modules()

# 清理旧的构建文件
if os.path.exists("build"):
    shutil.rmtree("build")
# 执行打包命令
subprocess.run(cmd, check=True)


print("打包完成!")
copy_modelscope()
print("modelscope 库复制完成!")
end_time = time.time()
total_time = end_time - start_time
print(f"总打包时间: {total_time:.2f} 秒")