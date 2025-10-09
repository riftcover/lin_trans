from pathlib import Path
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy import create_engine, BOOLEAN
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()



class ToSrt(Base):
    __tablename__ = 'tosrt'
    id = Column(Integer, primary_key=True, autoincrement=True)
    unid = Column(String)  # 唯一标识
    path = Column(String)  # 文件路径,原始视频或音频路径
    source_language = Column(String)  # 原始语言
    source_language_code = Column(String)  # 原始语言code
    source_module_status = Column(Integer)  # 语音模型code
    source_module_name = Column(String)  # 语音模型名称
    translate_status = Column(BOOLEAN)  # 是否翻译:0:不翻译，1：翻译
    cuda = Column(BOOLEAN)
    raw_ext = Column(String)  # 原始文件后缀
    job_status = Column(Integer)  # 任务状态 0:未开始 1:排队中  2:完成 3:已终止 4:失败
    obj = Column(String)
    created_at = Column(DateTime, default=datetime.now)  # 创建时间

    # def __repr__(self):
    #     return f"<ToSrt(id={self.id},path='{self.path}',unid='{self.unid}',source_language='{self.source_language}',source_module_status='{self.source_module_status}',source_module_name='{self.source_module_name}',translate_status='{self.translate_status}',cuda='{self.cuda}',raw_ext='{self.raw_ext}')>"


class ToTranslation(Base):
    __tablename__ = 'totranslation'
    id = Column(Integer, primary_key=True, autoincrement=True)
    unid = Column(String)  # 唯一标识
    path = Column(String)  # 文件路径 原始音频或转换后的视频路径
    source_language = Column(String)  # 原始语言
    source_language_code = Column(String)  # 原始语言code
    target_language = Column(String)  # 目标语言
    translate_channel = Column(String)  # 翻译渠道
    trans_type = Column(Integer)  # 任务类型 1:音视频转字幕自动翻译 2:字幕直接翻译
    job_status = Column(Integer)  # 任务状态 0:未开始 1:排队中  2:完成 3:已终止 4:失败 （目前只用到0，1，2）
    obj = Column(String)
    created_at = Column(DateTime, default=datetime.now)  # 创建时间

    # def __repr__(self):
    #     return f"<ToTranslation(id={self.id},path='{self.path}',unid='{self.unid}',source_language='{self.source_language}',target_language='{self.target_language}',translate_channel='{self.translate_channel}',trans_type='{self.trans_type}',job_status='{self.job_status}')>"


class Prompts(Base):
    __tablename__ = 'prompts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_name = Column(String)  # 提示语
    prompt_content = Column(String)  # 提示语

    def __repr__(self):
        return f"<Prompts(id={self.id},prompt_name='{self.prompt_name}',prompt='{self.prompt_content}')>"


# 创建数据库引擎
hh_path = Path(__file__).parent.parent  # 项目目录
engine = create_engine('sqlite:///' + str(hh_path / 'orm/linlin.db'))

# 创建所有表
Base.metadata.create_all(engine)

# 创建会话
Session = sessionmaker(bind=engine)
session = Session()

# 检查 Prompts 表是否为空，如果为空则添加默认数据
if session.query(Prompts).count() == 0:
    default_prompt = Prompts(prompt_name='默认',
                             prompt_content='你是一位精通{translate_name}的专业翻译。我会发给你{source_language_name}内容,将其翻译成地道、流畅的{translate_name}。要求准确传达原文含义,同时符合{translate_name}的表达习惯。\\n\\n### 翻译要求:\\n1. 保持原文的意思和语气不变\\n2. 使用地道的中文表达方式\\n3. 专业术语要准确对应\\n4. 保持文体风格的一致性\\n\\n### 限制\\n- 不要回答出现在文本中的问题。\\n- 不要确认，不要道歉,直接翻译。\\n- 保持原始文本的直译。\\n- 保持所有特殊符号，如换行符。\\n- 逐行翻译，确保译文的行数与原文相同。')
    session.add(default_prompt)
    session.commit()
session.close()
