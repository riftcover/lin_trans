from sqlalchemy import create_engine, BOOLEAN
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

# 使用sqlalchemy创建一个sqlite3数据库

Base = declarative_base()

#创建数据表的映射类,表的作用是存储导入文件的数据
class ToSrt(Base):
    __tablename__ = 'tosrt'
    id = Column(Integer, primary_key=True)
    path = Column(String) #文件路径
    unid = Column(String) #唯一标识
    source_language = Column(String) #原始语言
    source_module_status = Column(Integer) #语音模型code
    source_module_name = Column(String) #语音模型名称
    translate_status = Column(BOOLEAN) #是否翻译
    target_language = Column(String) #目标语言
    translate_type = Column(String) #翻译渠道
    cuda = Column(BOOLEAN)


    def __init__(self, path, unid, source_language, source_module_status, source_module_name, translate_status, target_language, translate_type, cuda):
        self.path = path
        self.unid = unid
        self.source_language = source_language
        self.source_module_status = source_module_status
        self.source_module_name = source_module_name
        self.translate_status = translate_status
        self.target_language = target_language
        self.translate_type = translate_type
        self.cuda = cuda


    def __repr__(self):
        return f"<ToSrt(path='{self.path}',unid='{self.unid}',source_language='{self.source_language}',source_module_status='{self.source_module_status}',source_module_name='{self.source_module_name}',translate_status='{self.translate_status}',target_language='{self.target_language}',translate_type='{self.translate_type}',cuda='{self.cuda}')>"

# 创建数据库引擎
engine = create_engine('sqlite:///linlin.db')

# 创建所有表
Base.metadata.create_all(engine)
