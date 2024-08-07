from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine, BOOLEAN
from sqlalchemy.orm import declarative_base

from nice_ui.configure.config import root_path

Base = declarative_base()


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
    obj = Column(String)

    # def __init__(self, unid, path, source_language, source_module_status, source_module_name, translate_status, cuda, raw_ext,obj, **kw: Any):
    #     super().__init__(**kw)
    #     self.unid = unid
    #     self.path = path
    #     self.source_language = source_language
    #     self.source_module_status = source_module_status
    #     self.source_module_name = source_module_name
    #     self.translate_status = translate_status
    #     self.cuda = cuda
    #     self.raw_ext = raw_ext
    #     self.job_status = 0
    #     self.obj = obj

    def __repr__(self):
        return f"<ToSrt(id={self.id},path='{self.path}',unid='{self.unid}',source_language='{self.source_language}',source_module_status='{self.source_module_status}',source_module_name='{self.source_module_name}',translate_status='{self.translate_status}',cuda='{self.cuda}',raw_ext='{self.raw_ext}')>"

class ToTranslation(Base):
    __tablename__ = 'totranslation'
    id = Column(Integer, primary_key=True, autoincrement=True)
    unid = Column(String)  #唯一标识
    path = Column(String)  # 文件路径 原始音频或转换后的视频路径
    source_language = Column(String)  # 原始语言
    target_language = Column(String)  #目标语言
    translate_type = Column(String)  #翻译渠道

    def __repr__(self):
        return f"<ToTranslation(id={self.id},path='{self.path}',unid='{self.unid}',source_language='{self.source_language}',target_language='{self.target_language}',translate_type='{self.translate_type}')>"


class Prompts(Base):
    __tablename__ = 'prompts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_name = Column(String)   #提示语
    prompt_content = Column(String)   #提示语

    # def __init__(self,prompt_name, prompt_content):
    #     self.prompt_name = prompt_name
    #     self.prompt_content = prompt_content

    def __repr__(self):
        return f"<Prompts(id={self.id},prompt_name='{self.prompt_name}',prompt='{self.prompt_content}')>"






# 创建数据库引擎

engine = create_engine('sqlite:///' + str(root_path/'orm/linlin.db'))


# 创建所有表
Base.metadata.create_all(engine)
