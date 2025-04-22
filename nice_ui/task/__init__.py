from enum import IntEnum


class WORK_TYPE(IntEnum):
    # 添加新的工作类型时，同时需要orm_factory.py中添加相应的映射关系（get_orm_by_work_type和set_orm_job_status方法）
    ASR = 1
    TRANS = 2
    ASR_TRANS = 3
    CLOUD_ASR =4
