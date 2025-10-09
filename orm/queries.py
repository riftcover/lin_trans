"""
ORM查询层 - 工程级最佳实践

设计原则（Linus式）:
1. "简单直接" - 不过度设计，解决实际问题
2. "显式优于隐式" - 调用者清楚看到发生了什么
3. "灵活但不复杂" - 支持简单和复杂场景
4. "向后兼容" - 渐进式迁移，不破坏现有代码

架构分层:
┌─────────────────────────────────────┐
│  应用层 (UI/Worker/TaskManager)     │
├─────────────────────────────────────┤
│  ORM类 (ToSrtOrm/ToTranslationOrm)  │  ← 向后兼容层
├─────────────────────────────────────┤
│  Repository (db.srt/db.translation) │  ← 推荐新代码使用
├─────────────────────────────────────┤
│  Session管理 (db.session())         │  ← 统一入口
├─────────────────────────────────────┤
│  SQLAlchemy Core                    │
└─────────────────────────────────────┘

使用场景:
1. 简单操作（90%场景）: 用ORM类，一行代码搞定
   orm.add_data_to_table(...)
   
2. 复杂事务（10%场景）: 用Repository，显式控制
   with db.session() as s:
       db.srt.create(s, ...)
       db.translation.create(s, ...)
"""
from datetime import datetime
from contextlib import contextmanager
from typing import List, Optional

from sqlalchemy.orm import sessionmaker, Session

from orm.inint import Prompts, engine, ToSrt, ToTranslation
from utils import logger


# ============================================================
# 核心：Session管理
# ============================================================

class SessionManager:
    """
    Session管理器 - 单例模式
    
    职责:
    - 创建和管理SessionFactory
    - 提供上下文管理器
    - 线程安全
    """
    _instance = None
    _session_factory = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._session_factory = sessionmaker(
                bind=engine,
                expire_on_commit=False  # 对象在commit后仍可访问
            )
        return cls._instance
    
    @contextmanager
    def session(self) -> Session:
        """
        获取数据库会话的上下文管理器
        
        使用:
            with session_manager.session() as s:
                # 数据库操作
                pass
        
        特性:
        - 线程安全（每次创建新session）
        - 自动commit成功的事务
        - 自动rollback失败的事务
        - 自动关闭session
        - 对象在session外仍可访问
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# 全局Session管理器实例
session_manager = SessionManager()


# ============================================================
# Repository层 - 纯数据访问逻辑
# ============================================================

class SrtRepository:
    """ASR任务仓库 - 静态方法，需要显式传session"""
    
    @staticmethod
    def create(session: Session, unid: str, path: str, 
               source_language: str, source_language_code: str,
               source_module_status: int, source_module_name: str,
               translate_status: bool, cuda: bool, raw_ext: str,
               job_status: int = 0, obj: str = "{}") -> ToSrt:
        """创建ASR任务"""
        task = ToSrt(
            unid=unid, path=path,
            source_language=source_language,
            source_language_code=source_language_code,
            source_module_status=source_module_status,
            source_module_name=source_module_name,
            translate_status=translate_status,
            cuda=cuda, raw_ext=raw_ext,
            job_status=job_status, obj=obj,
            created_at=datetime.now()
        )
        session.add(task)
        return task
    
    @staticmethod
    def find_all(session: Session) -> List[ToSrt]:
        """查询所有ASR任务"""
        return session.query(ToSrt).all()
    
    @staticmethod
    def find_by_unid(session: Session, unid: str) -> Optional[ToSrt]:
        """通过unid查找ASR任务"""
        result = session.query(ToSrt).filter(ToSrt.unid == unid).first()
        if result:
            logger.info(f'找到{unid}的数据')
        return result
    
    @staticmethod
    def find_untranslated(session: Session) -> List[ToSrt]:
        """查询未翻译的ASR任务"""
        return session.query(ToSrt).filter(
            ToSrt.translate_status == 0
        ).order_by(ToSrt.created_at.desc()).all()
    
    @staticmethod
    def update(session: Session, unid: str, **kwargs) -> bool:
        """更新ASR任务"""
        task = session.query(ToSrt).filter(ToSrt.unid == unid).first()
        if not task:
            logger.error(f"没有找到数据 unid: {unid}")
            return False
        
        for key, value in kwargs.items():
            setattr(task, key, value)
            logger.info(f'更新 {unid} 的数据：{key}:{value}')
        return True
    
    @staticmethod
    def delete(session: Session, unid: str) -> bool:
        """删除ASR任务"""
        task = session.query(ToSrt).filter(ToSrt.unid == unid).first()
        if not task:
            return False
        session.delete(task)
        return True


class TranslationRepository:
    """翻译任务仓库"""
    
    @staticmethod
    def create(session: Session, unid: str, path: str,
               source_language: str, source_language_code: str,
               target_language: str, translate_channel: str,
               trans_type: int, job_status: int,
               obj: str = "{}") -> ToTranslation:
        """创建翻译任务"""
        task = ToTranslation(
            unid=unid, path=path,
            source_language=source_language,
            source_language_code=source_language_code,
            target_language=target_language,
            translate_channel=translate_channel,
            trans_type=trans_type,
            job_status=job_status, obj=obj,
            created_at=datetime.now()
        )
        session.add(task)
        return task
    
    @staticmethod
    def find_all(session: Session) -> List[ToTranslation]:
        """查询所有翻译任务"""
        return session.query(ToTranslation).order_by(
            ToTranslation.created_at.desc()
        ).all()
    
    @staticmethod
    def find_by_unid(session: Session, unid: str) -> Optional[ToTranslation]:
        """通过unid查找翻译任务"""
        result = session.query(ToTranslation).filter(ToTranslation.unid == unid).first()
        if result:
            logger.info('找到数据')
        return result
    
    @staticmethod
    def update(session: Session, unid: str, **kwargs) -> bool:
        """更新翻译任务"""
        task = session.query(ToTranslation).filter(ToTranslation.unid == unid).first()
        if not task:
            logger.error(f"没有找到数据 unid: {unid}")
            return False
        
        for key, value in kwargs.items():
            setattr(task, key, value)
            logger.info(f'更新 {unid} 的数据：{key}:{value}')
        return True
    
    @staticmethod
    def delete(session: Session, unid: str) -> bool:
        """删除翻译任务"""
        task = session.query(ToTranslation).filter(ToTranslation.unid == unid).first()
        if not task:
            return False
        session.delete(task)
        return True


class PromptRepository:
    """Prompt仓库"""
    
    @staticmethod
    def create(session: Session, name: str, content: str) -> Prompts:
        """创建Prompt"""
        prompt = Prompts(prompt_name=name, prompt_content=content)
        session.add(prompt)
        return prompt
    
    @staticmethod
    def find_all(session: Session) -> List[Prompts]:
        """查询所有Prompts"""
        return session.query(Prompts).all()
    
    @staticmethod
    def find_by_id_gt_one(session: Session) -> List[Prompts]:
        """查询id大于1的Prompts"""
        return session.query(Prompts).filter(Prompts.id > 1).all()
    
    @staticmethod
    def find_names(session: Session) -> List:
        """查询所有Prompt名称（返回元组列表，兼容旧代码）"""
        return session.query(Prompts.prompt_name).all()
    
    @staticmethod
    def find_by_id(session: Session, prompt_id: int) -> Optional[Prompts]:
        """通过ID查找Prompt"""
        return session.query(Prompts).filter(Prompts.id == prompt_id).first()
    
    @staticmethod
    def find_by_name(session: Session, name: str) -> Optional[Prompts]:
        """通过名称查找Prompt"""
        return session.query(Prompts).filter_by(prompt_name=name).first()
    
    @staticmethod
    def update(session: Session, prompt_id: int, **kwargs) -> bool:
        """更新Prompt"""
        prompt = session.query(Prompts).filter(Prompts.id == prompt_id).first()
        if not prompt:
            return False
        
        for key, value in kwargs.items():
            setattr(prompt, key, value)
        return True
    
    @staticmethod
    def delete(session: Session, prompt_id: int) -> bool:
        """删除Prompt"""
        prompt = session.query(Prompts).filter(Prompts.id == prompt_id).first()
        if not prompt:
            return False
        session.delete(prompt)
        return True


# ============================================================
# ORM类 - 向后兼容层（推荐90%场景使用）
# ============================================================

class ToSrtOrm:
    """
    ASR任务ORM类 - 简化的API
    
    设计理念:
    - 每个方法自动管理session（适合简单操作）
    - 内部调用Repository（代码复用）
    - 保持原有API签名（向后兼容）
    
    适用场景:
    - 单个数据库操作
    - 不需要事务组合
    - 快速开发
    """
    
    def add_data_to_table(self, unid, path, source_language, source_language_code,
                          source_module_status, source_module_name, translate_status,
                          cuda, raw_ext, job_status=0, obj=None):
        """添加ASR任务"""
        if obj is None:
            obj = "{}"
        elif isinstance(obj, dict):
            import json
            obj = json.dumps(obj)
        with session_manager.session() as s:
            SrtRepository.create(
                s, unid, path, source_language, source_language_code,
                source_module_status, source_module_name, translate_status,
                cuda, raw_ext, job_status, obj
            )
    
    def query_data_all(self):
        """查询所有ASR任务"""
        with session_manager.session() as s:
            return SrtRepository.find_all(s)
    
    def query_data_by_unid(self, unid):
        """通过unid查询ASR任务"""
        with session_manager.session() as s:
            return SrtRepository.find_by_unid(s, unid)
    
    def query_data_format_unid_path(self):
        """查询未翻译的ASR任务"""
        with session_manager.session() as s:
            return SrtRepository.find_untranslated(s)
    
    def update_table_unid(self, unid, **kwargs):
        """更新ASR任务"""
        with session_manager.session() as s:
            return SrtRepository.update(s, unid, **kwargs)
    
    def delete_table_unid(self, unid):
        """删除ASR任务"""
        with session_manager.session() as s:
            return SrtRepository.delete(s, unid)


class ToTranslationOrm:
    """翻译任务ORM类 - 简化的API"""
    
    def add_data_to_table(self, unid, path, source_language, source_language_code,
                          target_language, translate_channel, trans_type, job_status, obj=None):
        """添加翻译任务"""
        if obj is None:
            obj = "{}"
        elif isinstance(obj, dict):
            import json
            obj = json.dumps(obj)
        with session_manager.session() as s:
            TranslationRepository.create(
                s, unid, path, source_language, source_language_code,
                target_language, translate_channel, trans_type, job_status, obj
            )
    
    def query_data_all(self):
        """查询所有翻译任务"""
        with session_manager.session() as s:
            return TranslationRepository.find_all(s)
    
    def query_data_by_unid(self, unid):
        """通过unid查询翻译任务"""
        with session_manager.session() as s:
            return TranslationRepository.find_by_unid(s, unid)
    
    def query_data_format_unid_path(self):
        """查询所有翻译任务（按时间倒序）"""
        with session_manager.session() as s:
            return TranslationRepository.find_all(s)
    
    def update_table_unid(self, unid, **kwargs):
        """更新翻译任务"""
        with session_manager.session() as s:
            return TranslationRepository.update(s, unid, **kwargs)
    
    def delete_table_unid(self, unid):
        """删除翻译任务"""
        with session_manager.session() as s:
            return TranslationRepository.delete(s, unid)


class PromptsOrm:
    """Prompt ORM类 - 简化的API"""
    
    def add_data_to_table(self, prompt_name: str, prompt_content: str):
        """添加Prompt"""
        with session_manager.session() as s:
            PromptRepository.create(s, prompt_name, prompt_content)
    
    def get_all_data(self):
        """获取所有Prompts"""
        with session_manager.session() as s:
            return PromptRepository.find_all(s)
    
    def get_data_with_id_than_one(self):
        """获取id大于1的Prompts"""
        with session_manager.session() as s:
            return PromptRepository.find_by_id_gt_one(s)
    
    def get_prompt_name(self):
        """获取所有Prompt名称（返回元组列表，兼容旧代码）"""
        with session_manager.session() as s:
            return PromptRepository.find_names(s)
    
    def query_data_by_id(self, key_id: int):
        """通过ID查询Prompt"""
        with session_manager.session() as s:
            return PromptRepository.find_by_id(s, key_id)
    
    def query_data_by_name(self, name: str):
        """通过名称查询Prompt"""
        with session_manager.session() as s:
            return PromptRepository.find_by_name(s, name)
    
    def update_table_prompt(self, key_id: int, **kwargs):
        """更新Prompt"""
        with session_manager.session() as s:
            return PromptRepository.update(s, key_id, **kwargs)
    
    def insert_table_prompt(self, prompt_name: str, prompt_content: str):
        """插入Prompt"""
        with session_manager.session() as s:
            PromptRepository.create(s, prompt_name, prompt_content)
        return True
    
    def delete_table_prompt(self, key_id):
        """删除Prompt"""
        with session_manager.session() as s:
            return PromptRepository.delete(s, key_id)


# ============================================================
# 便捷API - 用于复杂场景
# ============================================================

class Database:
    """
    数据库访问统一入口
    
    提供两种使用方式:
    1. 简单操作: 用ORM类
       orm = ToSrtOrm()
       orm.add_data_to_table(...)
    
    2. 复杂事务: 用Repository
       with db.session() as s:
           db.srt.create(s, ...)
           db.translation.create(s, ...)
    """
    
    # Session管理
    session = session_manager.session
    
    # Repository
    srt = SrtRepository
    translation = TranslationRepository
    prompt = PromptRepository


# 全局实例
db = Database()


# ============================================================
# 使用示例
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("ORM使用示例")
    print("=" * 60)
    
    # 示例1: 简单操作 - 用ORM类（推荐90%场景）
    print("\n【示例1】简单操作 - 用ORM类")
    print("-" * 60)
    
    orm = ToSrtOrm()
    orm.add_data_to_table(
        unid="test_123",
        path="/path/to/file.mp4",
        source_language="英语",
        source_language_code="en",
        source_module_status=1,
        source_module_name="test_module",
        translate_status=False,
        cuda=False,
        raw_ext=".mp4"
    )
    print("✓ 创建任务成功")
    
    task = orm.query_data_by_unid("test_123")
    print(f"✓ 查询任务成功: {task.path if task else 'None'}")
    
    orm.update_table_unid("test_123", job_status=2)
    print("✓ 更新任务成功")
    
    orm.delete_table_unid("test_123")
    print("✓ 删除任务成功")
    
    # 示例2: 复杂事务 - 用Repository（10%场景）
    print("\n【示例2】复杂事务 - 用Repository")
    print("-" * 60)
    
    with db.session() as s:
        # 在同一个事务中创建ASR任务和翻译任务
        srt_task = db.srt.create(
            s,
            unid="test_456",
            path="/path/to/file2.mp4",
            source_language="英语",
            source_language_code="en",
            source_module_status=1,
            source_module_name="test_module",
            translate_status=True,
            cuda=False,
            raw_ext=".mp4"
        )
        
        trans_task = db.translation.create(
            s,
            unid="test_456",
            path="/path/to/file2.mp4",
            source_language="英语",
            source_language_code="en",
            target_language="中文",
            translate_channel="openai",
            trans_type=1,
            job_status=0
        )
        
        print(f"✓ 在一个事务中创建了两个任务: {srt_task.unid}, {trans_task.unid}")
    
    # 清理
    with db.session() as s:
        db.srt.delete(s, "test_456")
        db.translation.delete(s, "test_456")
    print("✓ 清理完成")
    
    print("\n" + "=" * 60)
    print("所有示例执行成功！")
    print("=" * 60)
