import os
import shutil
import subprocess
import sys
import platform

# 检查并安装必要的模块
def install_required_modules():
    required_modules = [
        "better_ffmpeg_progress", "colorthief", "darkdetect",
        "httpx", "loguru", "modelscope", "numpy", "openai",
        "packaging", "path", "Pillow", "plyer", "pydantic", "pydub", "PySide6",
        "requests", "scipy", "sqlalchemy", "watchdog", "zhipuai", "socksio"
    ]
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            print(f"正在安装 {module}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])

# 安装必要的模块
install_required_modules()

# 清理旧的构建文件
if os.path.exists("dist"):
    shutil.rmtree("dist")

# 基本的 Nuitka 打包命令
cmd = [
    "python", "-m", "nuitka",
    "--standalone",
    "--remove-output",
    "--nofollow-import-to=torch,torchaudio",  # 排除torch和torchaudio
    "--include-module=better_ffmpeg_progress",
    "--include-module=colorthief",
    "--include-module=darkdetect",
    "--include-module=httpx",
    "--include-module=loguru",
    "--include-module=modelscope",
    "--include-module=numpy",
    "--include-module=openai",
    "--include-module=packaging",
    "--include-module=path",
    "--include-module=PIL",
    "--include-module=plyer",
    "--include-module=pydantic",
    "--include-module=pydub",
    "--include-module=PySide6",
    "--include-module=scipy",
    "--include-module=sqlalchemy",
    "--include-module=zhipuai",
    "--include-module=socksio",
    "--python-flag=no_site",
    "--enable-plugin=pyside6",
    "--output-dir=dist",
]

# 根据操作系统添加特定选项
if platform.system() == "Windows":
    cmd.append("--windows-disable-console")
elif platform.system() == "Darwin":  # macOS
    cmd.extend([
        "--macos-create-app-bundle",
        "--macos-disable-console",
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

print("打包完成!")