import os
import sys
import shutil
from pathlib import Path


def clean_text_folders():
    # 获取site-packages路径
    site_packages = r'D:\tool\build3\site-packages'
    print(f"正在清理目录: {site_packages}")

    # 计数器
    deleted_count = 0

    # 要删除的文件夹名称列表
    # folders_to_delete = ['test', 'tests', 'testing', 'doc','__pycache__']
    folders_to_delete = ['__pycache__']

    def should_delete_folder(folder_name):
        return any(target in folder_name.lower() for target in folders_to_delete)

    # 使用listdir而不是walk，这样可以更好地控制遍历
    def scan_directory(directory):
        nonlocal deleted_count
        try:
            # 获取目录中的所有内容
            items = os.listdir(directory)

            # 首先处理子目录
            for item in items:
                full_path = os.path.join(directory, item)
                if os.path.isdir(full_path):
                    # 检查当前目录名是否应该被删除
                    if should_delete_folder(item):
                        try:
                            print(f"正在删除: {full_path}")
                            shutil.rmtree(full_path)
                            deleted_count += 1
                        except Exception as e:
                            print(f"删除失败 {full_path}: {str(e)}")
                    else:
                        # 递归处理子目录
                        scan_directory(full_path)
        except Exception as e:
            print(f"访问目录失败 {directory}: {str(e)}")

    # 开始扫描
    scan_directory(str(site_packages))
    print(f"\n清理完成！共删除 {deleted_count} 个文件夹")


if __name__ == "__main__":
    clean_text_folders()