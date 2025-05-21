import os
import shutil
import subprocess
import sys
import platform
import argparse
import time
import fnmatch
import pkgutil
from nice_ui.ui import __version__

# 添加命令行参数解析
parser = argparse.ArgumentParser(description='增量编译应用程序')
parser.add_argument('--debug', action='store_true', help='启用调试模式')
parser.add_argument('--full', action='store_true', help='执行完整编译（包括第三方库）')
parser.add_argument('--clean', action='store_true', help='清理之前的编译文件')
args = parser.parse_args()

# 定义版本号
your_version = __version__  # 替换为您的实际版本号

# 定义项目根目录和其他目录
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
MODELS_DIR = os.path.join(PROJECT_ROOT, 'models')
RESULT_DIR = os.path.join(PROJECT_ROOT, 'result')
NICE_UI_DIR = os.path.join(PROJECT_ROOT, 'nice_ui')
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
ORM_DIR = os.path.join(PROJECT_ROOT, 'orm')
SPEC_FILE = os.path.join(PROJECT_ROOT, 'LinLin.spec')

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"创建目录: {directory}")

# 确保必要的目录存在
ensure_dir(RESULT_DIR)
ensure_dir(LOGS_DIR)
ensure_dir(MODELS_DIR)

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

# 检查 spec 文件是否存在
if not os.path.exists(SPEC_FILE):
    print("未找到 spec 文件，正在创建...")
    try:
        subprocess.run([sys.executable, "create_spec.py"] + (["--debug"] if args.debug else []), check=True)
    except subprocess.CalledProcessError as e:
        print(f"创建 spec 文件失败: {e}")
        sys.exit(1)

# 清理旧的构建文件
if args.clean:
    print("清理旧的构建文件...")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    clean_logs_directory()

# 执行打包命令
start_time = time.time()

print("开始打包...")

# 构建 PyInstaller 命令
cmd = [
    sys.executable,
    "-m", "PyInstaller",
    SPEC_FILE,
    "--noconfirm",  # 不询问确认
]

if args.debug:
    cmd.extend([
        "--debug=all",
        "--log-level=DEBUG",
    ])

# 如果是完整编译，添加 --clean 参数
if args.full:
    cmd.append("--clean")

# 执行 PyInstaller 命令
subprocess.run(cmd, check=True)

print("打包完成!")

# 复制模型库到 _internal 目录，并排除不必要的文件
def copy_models():
    # 如果不是完整编译，且目标目录已存在，则跳过
    if not args.full and os.path.exists(os.path.join("dist", "LinLin", "_internal")):
        print("跳过复制模型库（增量编译模式）")
        return

    # 要排除的目录和文件模式
    exclude_dirs = [
        'docs', 'test', 'tests', 'examples', 'sample', 'samples',
        '.git', '.github', '__pycache__', 'egg-info', 'dist-info',
        'bin', 'datasets', 'train'
    ]
    exclude_files = [
        '*.pyc', '*.pyo', '*.pyd', '*.so', '*.a', '*.lib',
        '*.md', '*.rst', '*.txt', '*.html', '*.pdf'
    ]
    
    # 特定库的排除目录
    specific_excludes = {
        'torch': ['test', 'testing', 'optim', 'distributed', 'utils/data', 'onnx', 'profiler'],
        'modelscope': ['examples', 'metrics', 'trainers', 'utils/test_utils'],
        'funasr': ['bin', 'datasets', 'train'],
        'scipy': ['optimize', 'spatial', 'stats', 'cluster', 'fft', 'integrate', 'interpolate', 'io', 'linalg', 'misc', 'ndimage', 'odr', 'signal', 'sparse', 'special'],
        'numpy': ['distutils', 'doc', 'f2py', 'testing', 'typing']
    }

    model_lists = ['modelscope', 'funasr']
    for model in model_lists:
        # 获取库的路径
        model_path = pkgutil.get_loader(model).path
        if not model_path:
            print(f"无法找到 {model} 库路径")
            continue
        try:
            # 获取包的根目录
            model_root = os.path.dirname(model_path)
            print(f"{model} 库路径: {model_root}")

            # 目标路径 (_internal 目录)
            target_path = os.path.join("dist", "LinLin", "_internal", model)

            # 确保目标目录存在
            os.makedirs(target_path, exist_ok=True)

            # 复制库目录，排除不必要的文件
            def custom_ignore(src, names):
                ignored_names = []
                
                # 检查是否在排除目录列表中
                for name in names:
                    full_path = os.path.join(src, name)
                    # 排除目录
                    if os.path.isdir(full_path):
                        if any(exclude in name for exclude in exclude_dirs):
                            ignored_names.append(name)
                            continue
                        
                        # 检查特定库的排除目录
                        for lib, excludes in specific_excludes.items():
                            if lib in src:
                                rel_path = os.path.relpath(full_path, model_root)
                                for exclude in excludes:
                                    if exclude in rel_path:
                                        ignored_names.append(name)
                                        break
                    # 排除文件
                    elif os.path.isfile(full_path):
                        if any(fnmatch.fnmatch(name, pattern) for pattern in exclude_files):
                            ignored_names.append(name)
                
                return ignored_names

            # 使用自定义忽略函数复制文件
            shutil.copytree(model_root, target_path, ignore=custom_ignore, dirs_exist_ok=True)

            print(f"{model} 库已复制到: {target_path} (排除了不必要的文件)")

        except Exception as e:
            print(f"复制 {model} 库时出错: {e}")

# 复制模型库（仅在完整编译或目标目录不存在时）
copy_models()

end_time = time.time()
total_time = end_time - start_time
hours, rem = divmod(total_time, 3600)
minutes, seconds = divmod(rem, 60)
print(f"总打包时间: {int(hours):02d}:{int(minutes):02d}:{seconds:05.2f}")

print("\n增量编译完成！")
print("如果您只修改了项目文件，下次可以不使用 --full 参数，以加快编译速度。")
print("如果您更新了第三方库或需要完整重新编译，请使用 --full 参数。")
