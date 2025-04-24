from app.cloud_asr.task_manager import get_task_manager

file = "C:/Users/gaosh/Downloads/Video/tt.wav"

# 获取任务管理器实例
task_manager = get_task_manager()

# 创建ASR任务，可以使用本地文件路径
task_id = task_manager.create_task(
    audio_file=file,  # 本地文件路径
    language="zh",  # 语言代码，'zh'表示中文
    unid="unique_identifier"  # 应用内唯一标识符
)

# 提交任务，会自动上传文件到OSS并获取URL
task_manager.submit_task(task_id)

# 获取任务状态
task = task_manager.get_task(task_id)
print(f"任务状态: {task.status}, 进度: {task.progress}%")