import time
import sys
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess


class ResourceHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("lin_resource.qrc"):
            print(f"Detected change in {event.src_path}")

            # 构建 pyside6-rcc 的完整路径
            python_path = sys.executable
            rcc_path = os.path.join(os.path.dirname(python_path), "Scripts", "pyside6-rcc.exe")

            try:
                subprocess.run([rcc_path, "lin_resource.qrc", "-o", "lin_resource_rc.py"], check=True)
                print("Resources updated.")
            except subprocess.CalledProcessError as e:
                print(f"Error updating resources: {e}")
            except FileNotFoundError:
                print(f"Could not find pyside6-rcc at {rcc_path}. Please check your PySide6 installation.")


if __name__ == "__main__":
    event_handler = ResourceHandler()
    observer = Observer()
    observer.schedule(event_handler, path='../components', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()