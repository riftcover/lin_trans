import os
import shutil
import subprocess
import sys
import platform
import argparse
import time
import pkgutil
import fnmatch
from pathlib import Path
from nice_ui.ui import __version__

# 添加命令行参数解析
parser = argparse.ArgumentParser(description='构建应用程序')
parser.add_argument('--debug', action='store_true', help='启用调试模式')
parser.add_argument('--no-installer', action='store_true', help='不创建安装包（DMG/EXE）')
parser.add_argument('--dmg-only', action='store_true', help='仅创建 DMG（macOS）')
parser.add_argument('--installer-only', action='store_true', help='仅创建安装包（Windows）')
parser.add_argument('--clean', action='store_true', help='清理缓存，强制重新分析依赖（生产构建推荐）')
parser.add_argument('--reuse-analysis', action='store_true', help='复用 Analysis 缓存，加快构建速度（开发阶段推荐）')
args = parser.parse_args()

# 定义版本号
your_version = __version__  # 替换为您的实际版本号

# 定义项目根目录和其他目录
PROJECT_ROOT = Path(__file__).resolve().parent
MODELS_DIR = PROJECT_ROOT / 'models'
RESULT_DIR = PROJECT_ROOT / 'result'
NICE_UI_DIR = PROJECT_ROOT / 'nice_ui'
LOGS_DIR = PROJECT_ROOT / 'logs'
ORM_DIR = PROJECT_ROOT / 'orm'


def ensure_dir(directory: Path):
    directory = Path(directory)
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
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
    "numpy/doc", "numpy/f2py", "numpy/testing", "numpy/typing"
]

# PyInstaller 打包命令
cmd = [
    sys.executable,
    "-m", "PyInstaller",
    "--name=Lapped",
    "--onedir",
    "--noconsole",
    "--windowed",  # 注释掉 --windowed 参数，允许显示控制台
    f"--add-data={os.path.join('orm', 'linlin.db')}{os.pathsep}orm",
    # 注意：models 目录不再打包到 .app 内部，而是使用 ~/Library/Application Support/Lapped/models/
    # f"--add-data=models{os.pathsep}models",  # ← 已移除
    f"--add-data={os.path.join('nice_ui', 'language')}{os.pathsep}{os.path.join('nice_ui', 'language')}",
    f"--add-data=logs{os.pathsep}logs",
    f"--add-data=result{os.pathsep}result",
    f"--add-data=.credentials{os.pathsep}.credentials",
    f"--add-data=config{os.pathsep}config",
    # 使用自定义 Hook 文件自动处理 FunASR 和其他依赖
    f"--additional-hooks-dir=hooks",
    # 包含基础的隐式导入（Hook 文件会自动处理 FunASR）
    # f"--hidden-import=distutils",
    # f"--hidden-import=distutils.util",
    # f"--hidden-import=distutils.version",
    # f"--hidden-import=distutils.spawn",
    # f"--hidden-import=distutils.sysconfig",
    # f"--hidden-import=distutils.core",
    # f"--hidden-import=setuptools",
    # f"--hidden-import=pkg_resources",
    # f"--hidden-import=packaging",
    # f"--hidden-import=packaging.version",
    "--noconfirm",  # 不询问确认
]

# 根据参数决定是否清理缓存
if args.clean:
    cmd.append("--clean")  # 强制清理，重新分析所有依赖
elif not args.reuse_analysis:
    # 默认行为：清理 dist/ 但保留 build/ 以复用 Analysis
    pass  # 不添加 --clean 参数

# 添加所有排除模式
for pattern in exclude_patterns:
    cmd.append(f"--exclude={pattern}")

# todo: 打包前重新生成orm/linlin.db文件
#todo: console不输出内容

# modelscope_path = pkgutil.get_loader("modelscope").path
# for _, name, _ in pkgutil.walk_packages([modelscope_path]):
#     cmd.append(f"--hidden-import=modelscope.{name}")

if args.debug:
    cmd.extend([
        "--debug=all",
        "--log-level=DEBUG",
    ])

# 根据操作系统添加特定选项
if platform.system() == "Windows":
    cmd.extend([f'--icon={Path("components") / "assets" / "lapped.ico"}'])
elif platform.system() == "Darwin":  # macOS
    cmd.extend([f'--icon={Path("components") / "assets" / "lapped.icns"}'])
    if platform.machine() == "arm64":
        cmd.append("--target-architecture=arm64")
    else:
        cmd.append("--target-architecture=x86_64")

# 添加主文件路径
cmd.append("run.py")


def clean_logs_directory():
    """清空 logs 文件夹中的所有文件，但保留文件夹"""
    # 确保 logs 目录存在
    if not LOGS_DIR.exists():
        print(f"创建 logs 目录: {LOGS_DIR}")
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        return

    # 删除 logs 目录中的所有文件和子目录
    for item in LOGS_DIR.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
    print("logs 目录已清空")

    for item in RESULT_DIR.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
    print("result 目录已清空")


# 执行打包命令
start_time = time.time()

# 清理旧的构建文件和日志
dist_dir = Path("dist")
if dist_dir.exists():
    shutil.rmtree(dist_dir)
    print("已清理 dist/ 目录")

# 如果指定了 --clean，也清理 build/ 目录
if args.clean:
    build_dir = Path("build")
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("已清理 build/ 目录（强制重新分析）")
else:
    print("保留 build/ 目录以复用 Analysis 缓存（加快构建速度）")

clean_logs_directory()

print("开始打包...")
print(f"PyInstaller 命令: {' '.join(cmd)}")
# 执行 PyInstaller 命令，捕获输出以便调试
result = subprocess.run(cmd, capture_output=False, text=True)
if result.returncode != 0:
    print(f"❌ PyInstaller 失败，退出码: {result.returncode}")
    sys.exit(1)

print("打包完成!")


# 复制模型库到 _internal 目录，并排除不必要的文件
def copy_models():
    # 要排除的目录和文件模式
    exclude_dirs = [
        'docs', 'test', 'tests', 'examples', 'sample', 'samples',
        '.git', '.github', '__pycache__', 'egg-info', 'dist-info',
        'bin', 'datasets', 'train'
    ]
    exclude_files = [
    ]

    # 特定库的排除目录
    specific_excludes = {
        # 'torch': ['test', 'testing', 'optim', 'distributed', 'utils/data', 'onnx', 'profiler'],
        # 'modelscope': ['examples', 'metrics', 'trainers', 'utils/test_utils'],
        # 'funasr': ['bin', 'datasets', 'train'],
        # 'scipy': ['optimize', 'spatial', 'stats', 'cluster', 'fft', 'integrate', 'interpolate', 'io', 'linalg', 'misc', 'ndimage', 'odr', 'signal', 'sparse', 'special'],
        # 'numpy': ['doc', 'f2py', 'testing', 'typing']
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
            model_root = Path(model_path).parent
            print(f"{model} 库路径: {model_root}")

            # 目标路径 (_internal 目录)
            target_path = Path("dist") / "Lapped" / "_internal" / model

            # 确保目标目录存在
            target_path.mkdir(parents=True, exist_ok=True)

            # 复制库目录，排除不必要的文件
            def custom_ignore(src, names):
                ignored_names = []

                # 检查是否在排除目录列表中
                for name in names:
                    full_path = Path(src) / name
                    # 排除目录
                    if full_path.is_dir():
                        if any(exclude in name for exclude in exclude_dirs):
                            ignored_names.append(name)
                            continue

                        # 检查特定库的排除目录
                        for lib, excludes in specific_excludes.items():
                            if lib in src:
                                rel_path = full_path.relative_to(model_root)
                                for exclude in excludes:
                                    if exclude in str(rel_path):
                                        ignored_names.append(name)
                                        break
                    # 排除文件
                    elif full_path.is_file():
                        if any(fnmatch.fnmatch(name, pattern) for pattern in exclude_files):
                            ignored_names.append(name)

                return ignored_names

            # 使用自定义忽略函数复制文件
            shutil.copytree(model_root, target_path, ignore=custom_ignore, dirs_exist_ok=True)

            print(f"{model} 库已复制到: {target_path} (排除了不必要的文件)")

        except Exception as e:
            print(f"复制 {model} 库时出错: {e}")


# 复制 funasr 库
copy_models()

end_time = time.time()
total_time = end_time - start_time
hours, rem = divmod(total_time, 3600)
minutes, seconds = divmod(rem, 60)
print(f"总打包时间: {int(hours):02d}:{int(minutes):02d}:{seconds:05.2f}")

print("=" * 50)
print("\n运行方式:")
print(f"  相对路径: ./dist/Lapped/Lapped")
print(f"  相对路径: .\dist\Lapped\Lapped.exe")
print(f"  绝对路径: .{PROJECT_ROOT / 'dist' / 'Lapped' / 'Lapped'}")


# ============================================================================
# 创建安装包（DMG for macOS, Installer for Windows）
# ============================================================================

def create_macos_dmg():
    """创建 macOS DMG 镜像文件"""
    print("\n" + "=" * 60)
    print("创建 macOS DMG 镜像")
    print("=" * 60)

    app_path = PROJECT_ROOT / "dist" / "Lapped.app"
    # dmg_name = f"Lapped-{your_version}-macOS-{platform.machine()}.dmg"
    dmg_name = "Lapped AI setup.dmg"
    dmg_path = PROJECT_ROOT / "dist" / dmg_name
    temp_dmg = PROJECT_ROOT / "dist" / "temp.dmg"
    volume_name = f"Lapped {your_version}"

    # 调试：列出 dist 目录内容
    print(f"\n调试信息：dist/ 目录内容：")
    dist_dir = PROJECT_ROOT / "dist"
    if dist_dir.exists():
        for item in dist_dir.iterdir():
            print(f"  - {item.name} ({'目录' if item.is_dir() else '文件'})")
    else:
        print(f"  ✗ dist/ 目录不存在！")

    # 检查 .app 是否存在
    if not app_path.exists():
        print(f"\n✗ 错误: 未找到 {app_path}")
        print("  请先运行 PyInstaller 打包")

        # 尝试查找可能的 .app 位置
        possible_paths = [
            PROJECT_ROOT / "dist" / "Lapped" / "Lapped.app",
            PROJECT_ROOT / "dist" / "Lapped.app",
        ]
        print("\n尝试查找 .app 文件：")
        for p in possible_paths:
            print(f"  - {p}: {'✓ 存在' if p.exists() else '✗ 不存在'}")

        return False

    print(f"✓ 找到应用: {app_path}")

    try:
        # 1. 删除旧的 DMG（如果存在）
        if dmg_path.exists():
            print(f"删除旧的 DMG: {dmg_path}")
            dmg_path.unlink()
        if temp_dmg.exists():
            temp_dmg.unlink()

        # 2. 创建临时 DMG
        print(f"创建临时 DMG...")
        # 计算 .app 大小并添加 50MB 缓冲
        app_size_mb = sum(f.stat().st_size for f in app_path.rglob('*') if f.is_file()) / (1024 * 1024)
        dmg_size_mb = int(app_size_mb + 50)

        subprocess.run([
            "hdiutil", "create",
            "-size", f"{dmg_size_mb}m",
            "-fs", "HFS+",
            "-volname", volume_name,
            str(temp_dmg)
        ], check=True)

        # 3. 挂载临时 DMG
        print(f"挂载 DMG...")
        result = subprocess.run([
            "hdiutil", "attach",
            str(temp_dmg),
            "-readwrite",
            "-noverify",
            "-noautoopen"
        ], capture_output=True, text=True, check=True)

        # 从输出中提取挂载点
        mount_point = None
        for line in result.stdout.split('\n'):
            if '/Volumes/' in line:
                mount_point = line.split('\t')[-1].strip()
                break

        if not mount_point:
            raise Exception("无法确定 DMG 挂载点")

        print(f"✓ DMG 已挂载到: {mount_point}")

        # 4. 复制 .app 到 DMG
        print(f"复制应用到 DMG...")
        dest_app = Path(mount_point) / "Lapped.app"
        subprocess.run(["cp", "-R", str(app_path), str(dest_app)], check=True)

        # 5. 创建 Applications 符号链接（方便拖拽安装）
        print(f"创建 Applications 符号链接...")
        subprocess.run([
            "ln", "-s", "/Applications",
            str(Path(mount_point) / "Applications")
        ], check=True)

        # 6. 设置 DMG 窗口属性（可选，需要 AppleScript）
        # 检测是否在 CI 环境中（没有 GUI）
        is_ci = os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true'

        if not is_ci:
            print(f"设置 DMG 外观...")
            applescript = f'''
            tell application "Finder"
                tell disk "{volume_name}"
                    open
                    set current view of container window to icon view
                    set toolbar visible of container window to false
                    set statusbar visible of container window to false
                    set the bounds of container window to {{100, 100, 600, 400}}
                    set viewOptions to the icon view options of container window
                    set arrangement of viewOptions to not arranged
                    set icon size of viewOptions to 128
                    set position of item "Lapped.app" of container window to {{150, 150}}
                    set position of item "Applications" of container window to {{350, 150}}
                    close
                    open
                    update without registering applications
                    delay 2
                end tell
            end tell
            '''

            try:
                subprocess.run(["osascript", "-e", applescript], check=False)
            except Exception as e:
                print(f"  警告: 设置 DMG 外观失败: {e}")
        else:
            print(f"跳过 DMG 外观设置（CI 环境）")

        # 7. 卸载 DMG
        print(f"卸载 DMG...")
        subprocess.run(["hdiutil", "detach", mount_point], check=True)

        # 8. 转换为压缩的只读 DMG
        print(f"压缩 DMG...")
        subprocess.run([
            "hdiutil", "convert",
            str(temp_dmg),
            "-format", "UDZO",
            "-o", str(dmg_path)
        ], check=True)

        # 9. 删除临时 DMG
        temp_dmg.unlink()

        # 10. 显示结果
        dmg_size = dmg_path.stat().st_size / (1024 * 1024)
        print("\n" + "=" * 60)
        print("✓ DMG 创建成功！")
        print("=" * 60)
        print(f"文件名: {dmg_name}")
        print(f"路径: {dmg_path}")
        print(f"大小: {dmg_size:.2f} MB")
        print("\n安装方式:")
        print("  1. 双击 DMG 文件")
        print("  2. 将 Lapped.app 拖拽到 Applications 文件夹")
        print("=" * 60)

        return True

    except subprocess.CalledProcessError as e:
        print(f"\n✗ 创建 DMG 失败: {e}")
        print(f"  命令输出: {e.stderr if hasattr(e, 'stderr') else 'N/A'}")
        # 清理
        try:
            if mount_point:
                subprocess.run(["hdiutil", "detach", mount_point], check=False)
            if temp_dmg.exists():
                temp_dmg.unlink()
        except:
            pass
        return False
    except Exception as e:
        print(f"\n✗ 创建 DMG 时发生错误: {e}")
        return False


def create_windows_installer():
    """创建 Windows 安装程序（使用 Inno Setup）"""
    print("\n" + "=" * 60)
    print("创建 Windows 安装程序")
    print("=" * 60)

    exe_dir = PROJECT_ROOT / "dist" / "Lapped"
    exe_path = exe_dir / "Lapped.exe"

    # 检查 .exe 是否存在
    if not exe_path.exists():
        print(f"✗ 错误: 未找到 {exe_path}")
        print("  请先运行 PyInstaller 打包")
        return False

    print(f"✓ 找到可执行文件: {exe_path}")

    # 图标文件路径
    icon_path = PROJECT_ROOT / "components" / "assets" / "lapped.ico"
    if not icon_path.exists():
        print(f"⚠ 警告: 未找到图标文件 {icon_path}")
        icon_path = None

    # 创建 Inno Setup 脚本
    iss_script = f"""
; Lapped 安装脚本
; 由 install_build.py 自动生成

#define MyAppName "Lapped"
#define MyAppVersion "{your_version}"
#define MyAppPublisher "Lapped AI"
#define MyAppURL "https://www.lapped-ai.com/"
#define MyAppExeName "Lapped.exe"

[Setup]
AppId={{{{B8F3E9A1-5C2D-4F7E-9A3B-1D8E6C4F2A9B}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{userpf}}\\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
AllowNoIcons=yes
OutputDir={PROJECT_ROOT / "dist"}
OutputBaseFilename=Lapped AI setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
SetupIconFile={PROJECT_ROOT / "components/assets/lapped.ico"}

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked

[Files]
Source: "{exe_dir}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{group}}\\{{cm:UninstallProgram,{{#MyAppName}}}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent
"""

    iss_path = PROJECT_ROOT / "dist" / "lapped_installer.iss"

    try:
        # 写入 ISS 脚本
        print(f"生成 Inno Setup 脚本: {iss_path}")
        with open(iss_path, 'w', encoding='utf-8') as f:
            f.write(iss_script)

        # 查找 Inno Setup 编译器
        iscc_paths = [
            r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            r"C:\Program Files\Inno Setup 6\ISCC.exe",
            r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
            r"C:\Program Files\Inno Setup 5\ISCC.exe",
        ]

        iscc_exe = None
        for path in iscc_paths:
            if Path(path).exists():
                iscc_exe = path
                break

        if not iscc_exe:
            print("\n" + "!" * 60)
            print("警告: 未找到 Inno Setup")
            print("!" * 60)
            print("\n请安装 Inno Setup:")
            print("  1. 访问: https://jrsoftware.org/isdl.php")
            print("  2. 下载并安装 Inno Setup 6")
            print("  3. 重新运行此脚本")
            print(f"\n或者手动编译:")
            print(f"  1. 打开 Inno Setup")
            print(f"  2. 打开文件: {iss_path}")
            print(f"  3. 点击 Build -> Compile")
            print("=" * 60)
            return False

        print(f"✓ 找到 Inno Setup: {iscc_exe}")

        # 编译安装程序
        print(f"编译安装程序...")
        result = subprocess.run(
            [iscc_exe, str(iss_path)],
            capture_output=True,
            text=True,
            check=True
        )

        # 查找生成的安装程序
        # installer_name = f"Lapped-{your_version}-Windows-Setup.exe"
        installer_name = f"Lapped AI setup.exe"
        installer_path = PROJECT_ROOT / "dist" / installer_name

        if installer_path.exists():
            installer_size = installer_path.stat().st_size / (1024 * 1024)
            print("\n" + "=" * 60)
            print("✓ Windows 安装程序创建成功！")
            print("=" * 60)
            print(f"文件名: {installer_name}")
            print(f"路径: {installer_path}")
            print(f"大小: {installer_size:.2f} MB")
            print("\n安装方式:")
            print("  双击运行安装程序，按照向导完成安装")
            print("=" * 60)
            return True
        else:
            print(f"✗ 未找到生成的安装程序: {installer_path}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"\n✗ 编译安装程序失败: {e}")
        print(f"  输出: {e.stdout}")
        print(f"  错误: {e.stderr}")
        return False
    except Exception as e:
        print(f"\n✗ 创建安装程序时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


# 主流程：根据平台创建安装包
if not args.no_installer:
    print("\n" + "=" * 60)
    print("开始创建安装包...")
    print("=" * 60)

    success = False
    if platform.system() == "Darwin":  # macOS
        if not args.installer_only:
            success = create_macos_dmg()
            if not success:
                print("\n❌ DMG 创建失败！")
                sys.exit(1)
    elif platform.system() == "Windows":
        if not args.dmg_only:
            success = create_windows_installer()
            if not success:
                print("\n❌ Windows 安装程序创建失败！")
                sys.exit(1)
    else:
        print(f"✗ 不支持的平台: {platform.system()}")
        print("  仅支持 macOS 和 Windows")
        sys.exit(1)
