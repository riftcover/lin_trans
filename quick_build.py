#!/usr/bin/env python3
"""
Lin-Trans 快速构建脚本
简化版的 Nuitka 打包工具，适合快速测试和构建

使用方法:
    python quick_build.py          # 发布版本
    python quick_build.py --debug  # 调试版本
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def clean_build():
    """清理构建目录"""
    print("🧹 清理构建目录...")
    
    dirs_to_clean = ["dist", "build", "__pycache__"]
    patterns_to_clean = ["*.build", "*.dist", "*.onefile-build"]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   删除: {dir_name}")
    
    import glob
    for pattern in patterns_to_clean:
        for path in glob.glob(pattern):
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"   删除: {path}")


def build_nuitka(debug_mode=False):
    """使用 Nuitka 构建"""
    
    app_name = "LinTrans_Debug" if debug_mode else "LinTrans"

    cmd = [
        sys.executable, "-m", "nuitka",

        # 基本配置
        "run.py",
        f"--output-filename={app_name}",
        "--output-dir=dist",

        # 编译模式
        "--standalone",
        "--assume-yes-for-downloads",
        "--show-progress",

        # 控制台模式 (Windows)
        "--windows-console-mode=attach" if debug_mode else "--windows-console-mode=disable",
        
        # 优化
        "--optimization=2",
        "--python-flag=no_site",
        "--python-flag=no_warnings",
        
        # 插件
        "--enable-plugin=pyside6",
        "--enable-plugin=anti-bloat",
        
        # 包含项目包
        "--include-package=nice_ui",
        "--include-package=components",
        "--include-package=agent",
        "--include-package=app", 
        "--include-package=services",
        "--include-package=utils",
        "--include-package=orm",
        
        # 包含数据
        "--include-data-dir=components/assets=components/assets",
        "--include-data-dir=components/themes=components/themes",
        "--include-data-dir=config=config",
        
        # PySide6 插件
        "--include-qt-plugins=platforms",
        "--include-qt-plugins=imageformats",
        "--include-qt-plugins=iconengines",
        "--include-qt-plugins=styles",
        
        # 排除不需要的包
        "--nofollow-import-to=pytest",
        "--nofollow-import-to=unittest",
        "--nofollow-import-to=doctest",
        "--nofollow-import-to=tkinter",
        "--nofollow-import-to=matplotlib",
        "--nofollow-import-to=jupyter",
        
        # 排除大型包（运行时动态加载）
        "--nofollow-import-to=torch",
        "--nofollow-import-to=torchaudio",
        "--nofollow-import-to=scipy",
        "--nofollow-import-to=numpy",
        "--nofollow-import-to=modelscope",
        "--nofollow-import-to=funasr",
    ]
    
    print(f"🔨 开始构建 {'调试' if debug_mode else '发布'} 版本...")
    print("📋 构建命令:")
    print("   " + " \\\n   ".join(cmd))
    print()
    
    try:
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            print("\n🎉 构建成功!")
            
            # 显示结果信息
            exe_name = f"{app_name}.exe"
            exe_path = Path("dist") / exe_name
            
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"📦 可执行文件: {exe_path}")
                print(f"📏 文件大小: {size_mb:.1f} MB")
                
                print(f"\n📋 使用说明:")
                print(f"1. 运行 dist/{exe_name} 启动程序")
                if debug_mode:
                    print("2. 调试版本会显示控制台输出")
                else:
                    print("2. 发布版本不显示控制台窗口")
                print("3. 确保目标机器已安装 Visual C++ Redistributable")
            
            return True
        else:
            print(f"\n💥 构建失败，返回码: {result.returncode}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\n💥 构建失败: {e}")
        return False
    except KeyboardInterrupt:
        print("\n⏹️  构建被用户中断")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Lin-Trans 快速构建工具")
    parser.add_argument("--debug", "-d", action="store_true", help="构建调试版本")
    parser.add_argument("--clean", "-c", action="store_true", help="构建前清理")
    
    args = parser.parse_args()
    
    print("🚀 Lin-Trans 快速构建工具")
    print("=" * 40)
    
    # 检查入口文件
    if not Path("run.py").exists():
        print("❌ 入口文件 run.py 不存在")
        sys.exit(1)
    
    # 检查 Nuitka
    try:
        result = subprocess.run([sys.executable, "-m", "nuitka", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Nuitka: {result.stdout.strip()}")
        else:
            print("❌ Nuitka 未安装")
            print("请运行: pip install nuitka")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Nuitka 检查失败: {e}")
        sys.exit(1)
    
    # 清理构建目录
    if args.clean:
        clean_build()
    
    # 执行构建
    success = build_nuitka(debug_mode=args.debug)
    
    if success:
        print("\n✨ 构建完成!")
    else:
        print("\n💥 构建失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()
