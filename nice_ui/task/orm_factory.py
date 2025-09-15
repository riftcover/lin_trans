from typing import Optional, Tuple, Union

from nice_ui.task import WORK_TYPE
from orm.queries import ToSrtOrm, ToTranslationOrm
from utils import logger


class OrmFactory:
    """
    ORM工厂类，负责根据工作类型返回对应的ORM实例
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OrmFactory, cls).__new__(cls)
            cls._instance._srt_orm = ToSrtOrm()
            cls._instance._trans_orm = ToTranslationOrm()
        return cls._instance
    
    def get_orm_by_work_type(self, work_type: WORK_TYPE) -> Optional[Union[ToSrtOrm, ToTranslationOrm, Tuple[ToSrtOrm, ToTranslationOrm]]]:
        """
        根据工作类型获取对应的ORM实例
        
        Args:
            work_type: 工作类型
            
        Returns:
            对应的ORM实例或实例元组，如果工作类型未知则返回None
        """
        if work_type == WORK_TYPE.ASR:
            return self._srt_orm
        elif work_type == WORK_TYPE.TRANS:
            return self._trans_orm
        elif work_type == WORK_TYPE.ASR_TRANS:
            return self._srt_orm, self._trans_orm
        elif work_type == WORK_TYPE.CLOUD_ASR:
            return self._srt_orm
        elif work_type == WORK_TYPE.CLOUD_ASR_TRANS:
            return self._srt_orm, self._trans_orm
        else:
            logger.error(f"未知的工作类型: {work_type}，请在OrmFactory中添加对应的映射")
            return None
        
    def set_orm_job_status(self, work_type: WORK_TYPE) -> Optional[Union[ToSrtOrm, ToTranslationOrm]]:
        """设置orm任务状态"""
        if work_type in(WORK_TYPE.ASR, WORK_TYPE.ASR_TRANS, WORK_TYPE.CLOUD_ASR):
            return self._srt_orm
        elif work_type == WORK_TYPE.TRANS:
            return self._trans_orm
        else:
            logger.error(f"未知的工作类型: {work_type}，请在OrmFactory中添加对应的映射")
            return None
            
    def get_srt_orm(self) -> ToSrtOrm:
        """获取SRT ORM实例"""
        return self._srt_orm
        
    def get_trans_orm(self) -> ToTranslationOrm:
        """获取翻译ORM实例"""
        return self._trans_orm
