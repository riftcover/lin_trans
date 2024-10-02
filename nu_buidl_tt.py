import os
import subprocess
import sys
import shutil


def run_nuitka_build():
    # 获取当前脚本的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 主Python文件名
    main_file = "linlin.py"

    # Nuitka命令
    nuitka_command = [sys.executable, "-m", "nuitka", "--follow-imports",
                      "--plugin-enable=pyside6",
                      "--standalone",
                      "--output-dir=build",
        "--macos-create-app-bundle",  # 为macOS创建.app包
        "--macos-app-name=linlin", "--include-data-dir=logs=logs",  # 添加logs文件夹
        "linlin.py"]

    print("开始 Nuitka 构建...")
    # 运行Nuitka命令
    try:
        subprocess.run(nuitka_command, check=True)
        print("Nuitka 构建成功完成。")
    except subprocess.CalledProcessError as e:
        print(f"Nuitka 构建失败：{e}")
        sys.exit(1)


def create_dmg():
    # 应用程序名称
    app_name = "linlin"  # 使用 Nuitka 默认的输出名称

    # .app文件路径
    app_path = f"build/{app_name}.app"

    # 检查.app文件是否存在
    if not os.path.exists(app_path):
        print(f"错误：找不到 {app_path}。请确保 Nuitka 构建成功。")
        sys.exit(1)

    print(f"找到 .app 文件：{app_path}")

    # 创建DMG命令
    create_dmg_command = ["create-dmg", "--volname", f"{app_name} Installer", "--volicon", "data/linlin.icns",  # 确保你有一个icon.icns文件
        "--window-pos", "200", "120", "--window-size", "600", "300", "--icon-size", "100", "--icon", f"{app_name}.app", "175", "120", "--hide-extension",
        f"{app_name}.app", "--app-drop-link", "425", "120", f"{app_name}.dmg", app_path]

    print("开始创建 DMG...")
    # 运行创建DMG命令
    try:
        subprocess.run(create_dmg_command, check=True)
        print(f"DMG 文件 '{app_name}.dmg' 已成功创建。")
    except subprocess.CalledProcessError as e:
        print(f"创建 DMG 文件时出错：{e}")
        sys.exit(1)


if __name__ == "__main__":
    run_nuitka_build()  # if sys.platform == "darwin":  # 仅在macOS上创建DMG  #     create_dmg()