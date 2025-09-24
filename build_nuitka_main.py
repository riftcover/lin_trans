#!/usr/bin/env python3
"""
Lin-Trans Nuitka 打包脚本
使用 Nuitka 将 Python 应用程序编译为独立的可执行文件

作者: riftcover
版本: 1.0.0
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Optional


class NuitkaBuilder:
    """Nuitka 构建器"""
    
    def __init__(self, config_file: str = "nuitka_config.json"):
        self.project_root = Path.cwd()
        self.config_file = self.project_root / config_file
        self.config = self.load_config()
        self.python_exe = sys.executable
        self.platform = platform.system().lower()
        
    def load_config(self) -> Dict:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  配置文件加载失败: {e}")
                print("使用默认配置...")
        
        # 默认配置
        return {
            "app_name": "LappedAI",
            "entry_point": "run.py",
            "output_dir": "dist",
            "icon": None,
            "console_mode": "disable",
            "optimization_level": 2,
            "include_packages": [
                "nice_ui",
                "components", 
                "agent",
                "app",
                "services",
                "utils",
                "orm",
                "config"
            ],
            "include_data_dirs": [
                "components/assets",
                "components/themes",
                "config"
            ],
            "exclude_packages": [
                "pytest",
                "unittest", 
                "doctest",
                "tkinter",
                "matplotlib",
                "jupyter",
                "IPython",
                "notebook"
            ],
            "pyside6_plugins": [
                "platforms",
                "imageformats", 
                "iconengines",
                "styles"
            ]
        }
    
    def clean_build_dir(self):
        """清理构建目录"""
        build_dirs = [
            self.config["output_dir"],
            "build",
            "__pycache__",
            "*.build",
            "*.dist",
            "*.onefile-build"
        ]
        
        print("🧹 清理构建目录...")
        for pattern in build_dirs:
            if "*" in pattern:
                # 处理通配符模式
                import glob
                for path in glob.glob(pattern):
                    if os.path.exists(path):
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        else:
                            os.remove(path)
                        print(f"   删除: {path}")
            else:
                path = Path(pattern)
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    print(f"   删除: {path}")
    
    def build_nuitka_command(self, debug_mode: bool = False) -> List[str]:
        """构建 Nuitka 命令"""
        config = self.config

        # 基础命令
        cmd = [
            self.python_exe, "-m", "nuitka",

            # 基本配置
            config["entry_point"],
            f"--output-dir={config['output_dir']}",

            # 编译模式
            "--standalone",
            "--assume-yes-for-downloads",
            "--show-progress",
            "--show-memory",

            # 优化设置
            # f"--optimization={config['optimization_level']}",
            "--python-flag=no_site",
            "--python-flag=no_warnings",

            # 启用插件
            "--enable-plugin=pyside6",
            "--enable-plugin=anti-bloat",
        ]

        # 应用名称
        app_name = config["app_name"]
        if debug_mode:
            app_name += "_Debug"
        cmd.append(f"--output-filename={app_name}")

        # 控制台模式 (Windows)
        if debug_mode:
            cmd.append("--windows-console-mode=attach")
        elif config["console_mode"] == "disable":
            cmd.append("--windows-console-mode=disable")
        else:
            cmd.append(f"--windows-console-mode={config['console_mode']}")

        # 图标
        if config.get("icon") and Path(config["icon"]).exists():
            cmd.append(f"--windows-icon-from-ico={config['icon']}")

        # 包含包
        cmd.extend(
            f"--include-package={package}"
            for package in config["include_packages"]
        )
        # 包含数据目录
        cmd.extend(
            f"--include-data-dir={data_dir}={data_dir}"
            for data_dir in config["include_data_dirs"]
            if Path(data_dir).exists()
        )
        # Qt 插件
        cmd.extend(
            f"--include-qt-plugins={plugin}"
            for plugin in config.get("qt_plugins", [])
        )
        # 排除包
        cmd.extend(
            f"--nofollow-import-to={package}"
            for package in config["exclude_packages"]
        )
        # 特殊处理大型包 - 从配置文件读取
        nofollow_packages = config.get("nofollow_imports", [])
        if not nofollow_packages:
            # 如果配置文件中没有，使用默认列表
            nofollow_packages = ["torch", "torchaudio", "scipy", "numpy", "modelscope", "funasr"]

        cmd.extend(f"--nofollow-import-to={package}" for package in nofollow_packages)
        return cmd
    
    def build(self, debug_mode: bool = False) -> bool:
        """执行构建"""
        print(f"\n🔨 开始构建 {'调试' if debug_mode else '发布'} 版本...")
        
        # 构建命令
        cmd = self.build_nuitka_command(debug_mode)
        
        print("📋 构建命令:")
        print("   " + " \\\n   ".join(cmd))
        print()
        
        try:
            # 执行构建
            result = subprocess.run(cmd, check=True)
            
            if result.returncode == 0:
                print("\n🎉 构建成功!")
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
    
    def post_build_info(self, debug_mode: bool = False):
        """构建后信息"""
        app_name = self.config["app_name"]
        if debug_mode:
            app_name += "_Debug"
        
        if self.platform == "windows":
            exe_name = f"{app_name}.exe"
        else:
            exe_name = app_name
        
        exe_path = Path(self.config["output_dir"]) / exe_name
        
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n📦 可执行文件: {exe_path}")
            print(f"📏 文件大小: {size_mb:.1f} MB")
            
            print(f"\n📋 使用说明:")
            print(f"1. 将 {self.config['output_dir']} 目录复制到目标机器")
            print(f"2. 运行 {exe_name} 启动程序")
            
            if debug_mode:
                print("3. 调试版本会显示控制台输出")
                print("4. 从命令行运行可以看到详细日志")
            else:
                print("3. 发布版本不显示控制台窗口")
            
            if self.platform == "windows":
                print("4. 确保目标机器已安装 Visual C++ Redistributable")

            # 运行时依赖提示
            nofollow_packages = self.config.get("nofollow_imports", [])
            if nofollow_packages:
                print(f"\n⚠️  运行时依赖提醒:")
                print(f"以下包被排除在编译之外，需要在目标机器上安装:")
                for package in nofollow_packages:
                    print(f"   - {package}")
                print(f"\n💡 安装方法:")
                print(f"1. 运行 install_runtime_deps.py 脚本自动安装")
                print(f"2. 或手动执行: pip install -r runtime_requirements.txt")
        else:
            print(f"\n❌ 可执行文件未找到: {exe_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Lin-Trans Nuitka 打包工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python build_nuitka_main.py                    # 构建发布版本
  python build_nuitka_main.py --debug            # 构建调试版本
  python build_nuitka_main.py --clean            # 清理后构建
  python build_nuitka_main.py --config custom.json  # 使用自定义配置
        """
    )
    
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="构建调试版本（显示控制台）"
    )
    
    parser.add_argument(
        "--clean", "-c",
        action="store_true", 
        help="构建前清理旧文件"
    )
    
    parser.add_argument(
        "--config",
        default="nuitka_config.json",
        help="配置文件路径"
    )
    
    args = parser.parse_args()
    
    # 创建构建器
    builder = NuitkaBuilder(args.config)
    
    print("🚀 Lin-Trans Nuitka 构建工具")
    print("=" * 50)

    
    # 清理构建目录
    if args.clean:
        builder.clean_build_dir()
    
    # 执行构建
    success = builder.build(debug_mode=args.debug)
    
    if success:
        builder.post_build_info(debug_mode=args.debug)
        print("\n✨ 构建完成!")
    else:
        print("\n💥 构建失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()
