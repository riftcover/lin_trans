"""
任务状态常量定义

所有任务管理器共用的状态常量
"""


class TaskStatus:
    """任务状态常量（所有任务管理器通用）"""
    
    # 基础状态
    PENDING = "PENDING"          # 等待处理/提交
    UPLOADING = "UPLOADING"      # 上传中
    SUBMITTED = "SUBMITTED"      # 已提交
    
    # 处理状态
    RUNNING = "RUNNING"          # 运行中（阿里云ASR）
    PROCESSING = "PROCESSING"    # 处理中（Gladia ASR）
    SPLITING = "SPLITING"        # 分词中
    
    # 终态
    COMPLETED = "COMPLETED"      # 已完成
    FAILED = "FAILED"            # 失败


# 向后兼容：保留旧的类名
ASRTaskStatus = TaskStatus

