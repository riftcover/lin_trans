import time
import os
from app.cloud_asr.task_manager import get_task_manager, ASRTaskStatus
from utils import logger

# 设置文件路径
file = "C:/Users/gaosh/Downloads/Video/tt.wav"

# 获取任务管理器实例
task_manager = get_task_manager()

# 生成任务ID
import uuid
task_id = str(uuid.uuid4())

# 创建ASR任务，可以使用本地文件路径
task_manager.create_task(
    task_id=task_id,  # 任务ID
    audio_file=file,  # 本地文件路径
    language="zh",  # 语言代码，'zh'表示中文
)

print(f"\n创建ASR任务成功，任务ID: {task_id}")

# 提交任务，会自动上传文件到OSS并获取URL
print("\n开始提交ASR任务...")
task_manager.submit_task(task_id)

# 等待任务完成
print("\n等待ASR任务完成...")
max_wait_time = 300  # 最长等待时间（秒）
start_time = time.time()

while True:
    # 获取任务状态
    task = task_manager.get_task(task_id)
    print(f"\r任务状态: {task.status}, 进度: {task.progress}%", end="")

    # 检查任务是否完成或失败
    if task.status == ASRTaskStatus.COMPLETED:
        print("\n\n任务已完成!")
        break
    elif task.status == ASRTaskStatus.FAILED:
        print(f"\n\n任务失败: {task.error}")
        break

    # 检查是否超时
    if time.time() - start_time > max_wait_time:
        print("\n\n等待任务超时!")
        break

    # 等待一段时间再检查
    time.sleep(2)

# 如果任务完成，显示结果
if task.status == ASRTaskStatus.COMPLETED:
    print("\n转写结果:")


    # 显示结果文件路径
    json_file_path = f"{os.path.splitext(file)[0]}_asr_result.json"
    srt_file_path = f"{os.path.splitext(file)[0]}.srt"

    if os.path.exists(json_file_path):
        print(f"\nJSON结果文件: {json_file_path}")

    if os.path.exists(srt_file_path):
        print(f"SRT字幕文件: {srt_file_path}")