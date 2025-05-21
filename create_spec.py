import os
import sys
import platform
import argparse
import time
from nice_ui.ui import __version__

# 添加命令行参数解析
parser = argparse.ArgumentParser(description='创建 PyInstaller spec 文件')
parser.add_argument('--debug', action='store_true', help='启用调试模式')
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

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"创建目录: {directory}")

# 确保必要的目录存在
ensure_dir(RESULT_DIR)
ensure_dir(LOGS_DIR)
ensure_dir(MODELS_DIR)

# 定义要排除的文件和目录
# 排除文档和测试文件
exclude_patterns = [
    "docs", "xff", ".github", "test", "tests", "examples", "sample", "samples",
    "__pycache__", "*.dist-info", "*.egg-info",
    # 特定库的排除
    "torch/test", "torch/testing", "torch/optim", "torch/distributed", "torch/utils/data", "torch/onnx", "torch/profiler",
    "modelscope/examples", "modelscope/metrics", "modelscope/trainers", "modelscope/utils/test_utils",
    "funasr/bin", "funasr/datasets", "funasr/train",
    "scipy/optimize", "scipy/spatial", "scipy/stats", "scipy/cluster", "scipy/fft", "scipy/integrate",
    "scipy/interpolate", "scipy/io", "scipy/linalg", "scipy/misc", "scipy/ndimage", "scipy/odr",
    "scipy/signal", "scipy/sparse", "scipy/special",
    "numpy/distutils", "numpy/doc", "numpy/f2py", "numpy/testing", "numpy/typing"
]

# 创建 spec 文件内容
spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# 定义项目根目录
project_root = {repr(PROJECT_ROOT)}

# 定义数据文件
datas = [
    (os.path.join('orm', 'linlin.db'), 'orm'),
    ('models', 'models'),
    (os.path.join('nice_ui', 'language'), os.path.join('nice_ui', 'language')),
    ('logs', 'logs'),
    ('result', 'result'),
    ('tmp', 'tmp'),
    ('.credentials', '.credentials'),
    ('config', 'config'),
]

# 定义要排除的模块
excludes = [
    'tkinter', 'matplotlib', 'PyQt5', 'PyQt6', 'PySide2',
]

# 定义要排除的文件和目录
exclude_datas = {repr(exclude_patterns)}

# 定义隐式导入
hiddenimports = [
    'sqlalchemy.sql.default_comparator',
    'pydantic',
    'pydantic_settings',
    'dotenv',
    'pytz',
]

# 定义 a 分析对象
a = Analysis(
    ['run.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 应用排除规则
for pattern in exclude_datas:
    a.datas = [x for x in a.datas if not any(x[0].startswith(p) for p in exclude_datas)]

# 创建 pyz 对象
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 创建可执行文件
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LinLin',
    debug={args.debug},
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console={not args.debug},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon={repr(os.path.join("components", "assets", "linlin.ico")) if platform.system() == "Windows" else repr(os.path.join("components", "assets", "linlin.icns"))},
)

# 创建集合对象
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LinLin',
)

# 如果是 macOS，创建 app bundle
{'''
# 创建 macOS app bundle
app = BUNDLE(
    coll,
    name='LinLin.app',
    icon=os.path.join("components", "assets", "linlin.icns"),
    bundle_identifier=None,
    info_plist={{
        'CFBundleShortVersionString': ''' + repr(your_version) + ''',
        'CFBundleVersion': ''' + repr(your_version) + ''',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    }},
)
''' if platform.system() == "Darwin" else '# 非 macOS 系统，不创建 app bundle'}
"""

# 保存 spec 文件
spec_file = "LinLin.spec"
with open(spec_file, "w", encoding="utf-8") as f:
    f.write(spec_content)

print(f"已创建 spec 文件: {spec_file}")
print("现在您可以使用以下命令进行编译:")
print(f"  pyinstaller {spec_file} {'--debug' if args.debug else ''}")
