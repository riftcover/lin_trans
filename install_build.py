import os
import shutil
import subprocess
import sys
import platform
import argparse
import site
import time
import pkgutil
import logging

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
    "--console",
    f"--add-data={os.path.join('orm', 'linlin.db')}{os.pathsep}orm",
    f"--add-data=models{os.pathsep}models",
    f"--add-data={os.path.join('nice_ui', 'language')}{os.pathsep}{os.path.join('nice_ui', 'language')}",
    f"--add-data=logs{os.pathsep}logs",
    f"--add-data=result{os.pathsep}result",
]

# todo: 打包前重新生成orm/linlin.db文件，删除logs中的文件
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
        "--icon={}".format(os.path.join("components", "assets", "linlin.ico")),
    ])
elif platform.system() == "Darwin":  # macOS
    cmd.extend([
        "--icon={}".format(os.path.join("components", "assets", "linlin.icns"))
    ])
    if platform.machine() == "arm64":
        cmd.append("--target-architecture=arm64")
    else:
        cmd.append("--target-architecture=x86_64")

# 添加主文件路径
cmd.append("run.py")

def clean_logs_directory():
    """清空 logs 文件夹中的所有文件，但保留文件夹"""
    try:
        # 确保 logs 目录存在
        if not os.path.exists(LOGS_DIR):
            print(f"创建 logs 目录: {LOGS_DIR}")
            os.makedirs(LOGS_DIR)
            return

        # 删除 logs 目录中的所有文件和子目录
        for item in os.listdir(LOGS_DIR):
            item_path = os.path.join(LOGS_DIR, item)
            try:
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                print(f"已删除: {item_path}")
            except Exception as e:
                print(f"删除 {item_path} 时出错: {e}")

        print("logs 目录已清空")
    except Exception as e:
        print(f"清理 logs 目录时出错: {e}")

# 执行打包命令
start_time = time.time()

# 清理旧的构建文件
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")
clean_logs_directory()

print("开始打包...")
# 执行 PyInstaller 命令
subprocess.run(cmd, check=True)

print("打包完成!")


# 复制 funasr 库到 _internal 目录
def copy_models():

    model_lists = ['modelscope','funasr']
    for model in model_lists:
        # 获取 funasr 库的路径
        funasr_path = pkgutil.get_loader(model).path
        if not funasr_path:
            print("无法找到 funasr 库路径")
            return
        try:
            # 获取 funasr 包的根目录
            funasr_root = os.path.dirname(funasr_path)
            print(funasr_root)

            # 目标路径 (_internal 目录)
            target_path = os.path.join("dist", "LinLin", "_internal", model)

            # 确保目标目录存在
            os.makedirs(target_path, exist_ok=True)

            # 复制整个 funasr 目录
            shutil.copytree(funasr_root, target_path, dirs_exist_ok=True)

            print(f"{model} 库已复制到: {target_path}")

        except Exception as e:
            print(f"复制 funasr 库时出错: {e}")


# 复制 funasr 库
copy_models()

end_time = time.time()
total_time = end_time - start_time
hours, rem = divmod(total_time, 3600)
minutes, seconds = divmod(rem, 60)
print(f"总打包时间: {int(hours):02d}:{int(minutes):02d}:{seconds:05.2f}")

"""
2024-10-22 14:43:45.981 | DEBUG    | nice_ui.task.queue_worker:consume_queue:28 - 获取到任务:raw_name='F:/ski/国外教学翻译/Top 10 Affordable Ski Resorts in Europe.mp4' raw_dirname='F:/ski/国外教学翻译' raw_basename='Top 10 Affordable Ski Resorts in Europe.mp4' raw_noextname='Top 10 Affordable Ski Resorts in Europe' raw_ext='mp4' codec_type='video' output='C:/tool/linlin/scripts/result/2db4247eee62b0a4a56ca1e8acda7d48' wav_dirname='C:/tool/linlin/scripts/result/2db4247eee62b0a4a56ca1e8acda7d48/Top 10 Affordable Ski Resorts in Europe.wav' media_dirname='F:/ski/国外教学翻译/Top 10 Affordable Ski Resorts in Europe.mp4' srt_dirname='C:/tool/linlin/scripts/result/2db4247eee62b0a4a56ca1e8acda7d48/Top 10 Affordable Ski Resorts in Europe.srt' unid='2db4247eee62b0a4a56ca1e8acda7d48' source_mp4='F:/ski/国外教学翻译/Top 10 Affordable Ski Resorts in Europe.mp4' work_type=<WORK_TYPE.ASR: 1>

result 输出目录不对
"""

# # 在主程序 run.py 中添加以下代码来处理控制台输出
# if not os.path.exists('logs'):
#     os.makedirs('logs')

# class StreamToLogger:
#     def __init__(self, logger, log_level=logging.INFO):
#         self.logger = logger
#         self.log_level = log_level
#         self.linebuf = ''

#     def write(self, buf):
#         for line in buf.rstrip().splitlines():
#             self.logger.log(self.log_level, line.rstrip())

#     def flush(self):
#         pass

# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s:%(levelname)s:%(message)s',
#     filename='logs/output.log',
#     filemode='a'
# )

# stdout_logger = logging.getLogger('STDOUT')
# sl = StreamToLogger(stdout_logger, logging.INFO)
# sys.stdout = sl

# stderr_logger = logging.getLogger('STDERR')
# sl = StreamToLogger(stderr_logger, logging.ERROR)
# sys.stderr = sl
