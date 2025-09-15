from enum import IntEnum,StrEnum


class WORK_TYPE(IntEnum):
    # 添加新的工作类型时，同时需要orm_factory.py中添加相应的映射关系（get_orm_by_work_type和set_orm_job_status方法）
    ASR = 1
    TRANS = 2
    ASR_TRANS = 3
    CLOUD_ASR = 4
    CLOUD_ASR_TRANS = 5

class WORK_TYPE_NAME(StrEnum):
    """工作类型名称枚举"""
    ASR = "转录"
    TRANS = "翻译"
    ASR_TRANS = "转录双语"
    CLOUD_ASR = "转录"
    CLOUD_ASR_TRANS = "转录双语"

    @classmethod
    def get_name(cls, work_type: 'WORK_TYPE') -> str:
        """
        根据工作类型获取显示名称

        通过枚举名称自动映射，新增类型时只需要保持 WORK_TYPE 和 WORK_TYPE_NAME 的名称一致
        """
        try:
            # 通过名称自动映射，避免手动维护映射关系
            return getattr(cls, work_type.name)
        except (AttributeError, TypeError):
            return str(work_type)
