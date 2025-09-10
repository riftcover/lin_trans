import os
import sys
import subprocess
from pathlib import Path
import time

def install_whl():
        print("\n=== 开始安装依赖 ===")
        print(f"当前工作目录: {os.getcwd()}")
        print(f"Python解释器: {sys.executable}")
        
        python_path = Path(sys.exec_prefix).joinpath("python.exe")
        requirements_path = Path(sys.exec_prefix).parent.joinpath("scripts").joinpath("requirements.txt")
        site_packages = Path(sys.exec_prefix).joinpath("lib").joinpath("site-packages")
        wheels_dir = Path(sys.exec_prefix).parent.joinpath("wheels")
        
        print(f"\n=== 路径信息 ===")
        print(f"Python路径: {python_path}")
        print(f"Requirements路径: {requirements_path}")
        print(f"包安装路径: {site_packages}")
        print(f"Wheels目录: {wheels_dir}")
        
        
        # 切换到项目根目录
        project_root = Path(sys.exec_prefix).parent
        os.chdir(project_root)
        print(f"\n切换工作目录到: {project_root}")
        
        # 准备命令参数
        cmd = [
            str(python_path),
            "-m",
            "pip",
            "install",
            "--no-index",
            "--find-links",
            str(wheels_dir),
            "-r",
            str(requirements_path),
            "--target",
            str(site_packages),
            "--upgrade",
            "--force-reinstall"
        ]
        
        print("\n=== 执行安装命令 ===")
        print(f"命令: {' '.join(cmd)}")
        
        try:
            # 执行命令并实时输出结果
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW  # 避免弹出终端窗口
            )
            
            # 实时打印输出
            for line in process.stdout:
                print(line, end='')
                
            # 等待命令执行完成
            return_code = process.wait()
            
            if return_code == 0:
                print("\n=== 安装成功 ===")
            else:
                print(f"\n=== 安装失败，返回码: {return_code} ===")
                sys.exit(return_code)
                
        except Exception as e:
            print(f"\n=== 执行命令时发生错误: {str(e)} ===")
            sys.exit(1)

if __name__ == "__main__":
    install_whl()
