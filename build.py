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
        "scipy", "sqlalchemy", "zhipuai", "socksio"
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

# 添加命令行参数解析
parser = argparse.ArgumentParser(description='构建应用程序')
parser.add_argument('--debug', action='store_true', help='启用调试模式')
args = parser.parse_args()

# 基本的 Nuitka 打包命令
cmd = [
    sys.executable,
    "-m", "nuitka",
    "--standalone",
    "--remove-output",
    "--plugin-enable=pyside6",
    "--include-package=scipy",
    "--include-package=numpy",
    "--include-package=better_ffmpeg_progress",
    "--include-package=colorthief",
    "--include-package=darkdetect",
    "--include-package=httpx",
    "--include-package=loguru",
    "--include-package=modelscope",
    "--include-package=openai",
    "--include-package=packaging",
    "--include-package=path",
    "--include-package=pydantic",
    "--include-package=sqlalchemy",
    "--include-package=socksio",
    "--noinclude-pytest-mode=nofollow",
    "--nofollow-import-to=torch,torchaudio",  # 排除torch和torchaudio
    "--python-flag=no_site",
    "--output-dir=dist",
    "--include-data-dir=models=models",  # 包含models文件夹
    "--include-data-files=orm/linlin.db=orm/linlin.db",  # 包含linlin.db文件
]

# 在 cmd 列表中添加以下选项
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
    cmd.append("--windows-disable-console")
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

# 执行打包命令
subprocess.run(cmd, check=True)
# 复制 models 文件夹到打包目录
if platform.system() == "Darwin":  # macOS
    app_name = "run.app"  # 替换为您的应用程序名称
    models_src = "models"
    models_dst = os.path.join("dist", app_name, "Contents", "Resources", "models")
    if os.path.exists(models_src):
        shutil.copytree(models_src, models_dst, dirs_exist_ok=True)

    # 确保 orm 目录存在，并复制 linlin.db
    orm_dir = os.path.join("dist", app_name, "Contents", "Resources", "orm")
    os.makedirs(orm_dir, exist_ok=True)
    linlin_db_src = "orm/linlin.db"
    linlin_db_dst = os.path.join(orm_dir, "linlin.db")
    if os.path.exists(linlin_db_src):
        shutil.copy2(linlin_db_src, linlin_db_dst)
else:
    models_src = "models"
    models_dst = os.path.join("dist", "models")
    if os.path.exists(models_src):
        shutil.copytree(models_src, models_dst, dirs_exist_ok=True)

    # 确保 orm 目录存在，并复制 linlin.db
    orm_dir = os.path.join("dist", "orm")
    os.makedirs(orm_dir, exist_ok=True)
    linlin_db_src = "orm/linlin.db"
    linlin_db_dst = os.path.join(orm_dir, "linlin.db")
    if os.path.exists(linlin_db_src):
        shutil.copy2(linlin_db_src, linlin_db_dst)

print("打包完成!")