from typing import Any

from sqlalchemy import create_engine, BOOLEAN
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String

from nice_ui.configure.config import root_path

# 使用sqlalchemy创建一个sqlite3数据库

Base = declarative_base()


#创建数据表的映射类,表的作用是存储导入文件的数据
class ToSrt(Base):
    __tablename__ = 'tosrt'
    id = Column(Integer, primary_key=True, autoincrement=True)
    unid = Column(String)  #唯一标识
    path = Column(String)  #文件路径,原始视频或音频路径
    source_language = Column(String)  #原始语言
    source_module_status = Column(Integer)  #语音模型code
    source_module_name = Column(String)  #语音模型名称
    translate_status = Column(BOOLEAN)  #是否翻译
    cuda = Column(BOOLEAN)
    raw_ext = Column(String)  #原始文件后缀
    job_status = Column(Integer)  #任务状态 0:未开始 1:排队中  2:完成 3:已终止 4:失败

    def __init__(self, unid, path, source_language, source_module_status, source_module_name, translate_status, cuda, raw_ext, **kw: Any):
        super().__init__(**kw)
        self.unid = unid
        self.path = path
        self.source_language = source_language
        self.source_module_status = source_module_status
        self.source_module_name = source_module_name
        self.translate_status = translate_status
        self.cuda = cuda
        self.raw_ext = raw_ext
        self.job_status = 0

    def __repr__(self):
        return f"<ToSrt(path='{self.path}',unid='{self.unid}',source_language='{self.source_language}',source_module_status='{self.source_module_status}',source_module_name='{self.source_module_name}',translate_status='{self.translate_status}',cuda='{self.cuda}',raw_ext='{self.raw_ext}')>"

class ToTranslation(Base):
    __tablename__ = 'totranslation'
    id = Column(Integer, primary_key=True, autoincrement=True)
    unid = Column(String)  #唯一标识
    path = Column(String)  # 文件路径 原始音频或转换后的视频路径
    source_language = Column(String)  # 原始语言
    target_language = Column(String)  #目标语言
    translate_type = Column(String)  #翻译渠道

    def __init__(self, unid, path, source_language, target_language, translate_type, **kw: Any):
        super().__init__(**kw)
        self.unid = unid
        self.path = path
        self.source_language = source_language
        self.target_language = target_language
        self.translate_type = translate_type

    def __repr__(self):
        return f"<ToTranslation(path='{self.path}',unid='{self.unid}',source_language='{self.source_language}',target_language='{self.target_language}',translate_type='{self.translate_type}')>"

# 创建数据库引擎

engine = create_engine('sqlite:///' + str(root_path/'orm/linlin.db'))


# 创建所有表
Base.metadata.create_all(engine)
