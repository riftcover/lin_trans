import os
import shutil
import subprocess
import sys
import platform
import argparse
import site
import time
import pkgutil
# ... (保留现有的 import 语句和函数定义) ...

# 添加命令行参数解析
parser = argparse.ArgumentParser(description='构建应用程序')
parser.add_argument('--debug', action='store_true', help='启用调试模式')
args = parser.parse_args()

# 定义版本号
your_version = "0.1.0"  # 替换为您的实际版本号

# 定义项目根目录和其他目录
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
MODELS_DIR = os.path.join(PROJECT_ROOT, 'models')
RESULT_DIR = os.path.join(PROJECT_ROOT, 'result')
NICE_UI_DIR = os.path.join(PROJECT_ROOT, 'nice_ui')
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
ORM_DIR = os.path.join(PROJECT_ROOT, 'orm')


def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"创建目录: {directory}")
# 确保必要的目录存在
ensure_dir(RESULT_DIR)
ensure_dir(LOGS_DIR)
ensure_dir(MODELS_DIR)

# PyInstaller 打包命令
cmd = [
    sys.executable,
    "-m", "PyInstaller",
    "--name=LinLin",
    "--onedir",
    "--windowed",
    "--add-data=orm/linlin.db:orm",
    "--add-data=models:models",
    "--add-data=plugin:plugin",
    "--add-data=nice_ui/language:nice_ui/language",
    "--add-data=logs:logs",
    "--add-data=result:result",
    "--hidden-import=modelscope",
    # "--hidden-import=modelscope.hub",
    # "--hidden-import=modelscope.hub.snapshot_download",
]

# 添加 modelscope 的所有子模块
modelscope_path = pkgutil.get_loader("modelscope").path
for _, name, _ in pkgutil.walk_packages([modelscope_path]):
    cmd.append(f"--hidden-import=modelscope.{name}")

if args.debug:
    cmd.extend([
        "--debug=all",
        "--log-level=DEBUG",
    ])

# 根据操作系统添加特定选项
if platform.system() == "Windows":
    cmd.extend([
        "--icon=components/assets/linlin.ico",  # 添加 Windows 图标
    ])
elif platform.system() == "Darwin":  # macOS
    cmd.extend([
        "--icon=components/assets/linlin.icns",  # 添加 macOS 图标
    ])

# 添加主文件路径
cmd.append("run.py")

# 执行打包命令
start_time = time.time()

# 清理旧的构建文件
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")

# 执行 PyInstaller 命令
subprocess.run(cmd, check=True)

print("打包完成!")

# 复制额外的依赖项（如果需要）
# 例如，复制 modelscope 库（如果需要的话）
# copy_modelscope()

end_time = time.time()
total_time = end_time - start_time
hours, rem = divmod(total_time, 3600)
minutes, seconds = divmod(rem, 60)
print(f"总打包时间: {int(hours):02d}:{int(minutes):02d}:{seconds:05.2f}")


"""
2024-10-22 14:43:45.981 | DEBUG    | nice_ui.task.queue_worker:consume_queue:28 - 获取到任务:raw_name='F:/ski/国外教学翻译/Top 10 Affordable Ski Resorts in Europe.mp4' raw_dirname='F:/ski/国外教学翻译' raw_basename='Top 10 Affordable Ski Resorts in Europe.mp4' raw_noextname='Top 10 Affordable Ski Resorts in Europe' raw_ext='mp4' codec_type='video' output='C:/tool/linlin/scripts/result/2db4247eee62b0a4a56ca1e8acda7d48' wav_dirname='C:/tool/linlin/scripts/result/2db4247eee62b0a4a56ca1e8acda7d48/Top 10 Affordable Ski Resorts in Europe.wav' media_dirname='F:/ski/国外教学翻译/Top 10 Affordable Ski Resorts in Europe.mp4' srt_dirname='C:/tool/linlin/scripts/result/2db4247eee62b0a4a56ca1e8acda7d48/Top 10 Affordable Ski Resorts in Europe.srt' unid='2db4247eee62b0a4a56ca1e8acda7d48' source_mp4='F:/ski/国外教学翻译/Top 10 Affordable Ski Resorts in Europe.mp4' work_type=<WORK_TYPE.ASR: 1>

result 输出目录不对
"""