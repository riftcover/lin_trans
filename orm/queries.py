from functools import wraps

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker, scoped_session

from orm.inint import Prompts, engine, ToSrt, ToTranslation

# 创建一个数据库会话

SessionLocal = scoped_session(sessionmaker(bind=engine))


# SessionLocal = sessionmaker(bind=engine)


# 装饰器，用于创建数据库会话，并在函数执行完毕后关闭会话
def session_manager(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = SessionLocal()
        try:
            result = func(*args, **kwargs, session=session)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    return wrapper


class ToSrtOrm:
    # 添加ToSrt数据

    @session_manager
    def add_data_to_table(self, unid, path, source_language, source_module_status, source_module_name, translate_status, cuda, raw_ext, job_status=0, obj=None, session=None):
        if obj is None:
            obj = {}
        new_entry = ToSrt(unid=unid, path=path, source_language=source_language, source_module_status=source_module_status, source_module_name=source_module_name, translate_status=translate_status, cuda=cuda,
                          raw_ext=raw_ext, job_status=job_status, obj=obj, )
        session.add(new_entry)
        session.commit()

    @session_manager
    def get_all_data(self, session=None):
        return session.query(ToSrt).all()

    @session_manager
    def query_data_by_unid(self, unid, session=None):
        try:
            return session.query(ToSrt).filter_by(unid=unid).one()
        except NoResultFound:
            return None

    @session_manager
    def query_data_all(self, session=None):
        return session.query(ToSrt).all()

    @session_manager
    def query_data_format_unid_path(self, session=None):
        # 输出所有行的unid和path
        return session.query(ToSrt.unid, ToSrt.path, ToSrt.job_status).all()

    @session_manager
    def update_table_unid(self, unid, session=None, **kwargs):
        if entry := self.query_data_by_unid(unid):
            for key, value in kwargs.items():
                setattr(entry, key, value)
            session.commit()
            return True
        return False

    @session_manager
    def delete_table_unid(self, unid, session=None):
        if entry := self.query_data_by_unid(unid):
            session.delete(entry)
            session.commit()
            return True
        return False


# 添加


class ToTranslationOrm:
    # 添加ToTranslation数据
    @session_manager
    def add_to_translation(self, unid, path, source_language, target_language, translate_type, session=None):
        new_entry = ToTranslation(unid=unid, path=path, source_language=source_language, target_language=target_language, translate_type=translate_type, )
        session.add(new_entry)
        session.commit()

    @session_manager
    def get_all_to_translation(self, session=None):
        return session.query(ToTranslation).all()

    @session_manager
    def get_to_translation_by_unid(self, unid, session=None):
        try:
            return session.query(ToTranslation).filter_by(unid=unid).one()
        except NoResultFound:
            return None

    @session_manager
    def update_to_translation(self, unid, session=None, **kwargs):
        if entry := self.get_to_translation_by_unid(unid):
            for key, value in kwargs.items():
                setattr(entry, key, value)
            session.commit()
            return True
        return False

    @session_manager
    def delete_to_translation(self, unid, session=None):
        if entry := self.get_to_translation_by_unid(unid):
            session.delete(entry)
            session.commit()
            return True
        return False


class PromptsOrm:
    @session_manager
    def add_data_to_table(self, prompt_name: str, prompt_content: str, session=None):
        new_entry = Prompts(prompt_name=prompt_name, prompt_content=prompt_content)
        session.add(new_entry)
        session.commit()

    @session_manager
    def get_all_data(self, session=None):
        prompts = session.query(Prompts).all()
        # 确保所有相关的属性都被加载
        for prompt in prompts:
            session.refresh(prompt)
        # 将对象从会话中分离，但保留其数据
        session.expunge_all()
        return prompts

    # 获取表中id大于1的数据
    @session_manager
    def get_data_with_id_than_one(self, session=None):
        prompts = session.query(Prompts).filter(Prompts.id > 1).all()
        # 确保所有相关的属性都被加载
        for prompt in prompts:
            session.refresh(prompt)
        # 将对象从会话中分离，但保留其数据
        session.expunge_all()
        return prompts

    @session_manager
    def query_data_by_id(self, key_id: int, session=None):
        # 输入prompt_name查询数据
        try:
            prompt = session.query(Prompts).filter_by(id=key_id).one()
            session.refresh(prompt)
            session.expunge(prompt)
            return prompt
        except NoResultFound:
            return None

    @session_manager
    def update_table_prompt(self, key_id: int, session=None, **kwargs, ):
        if entry := self.query_data_by_id(key_id):
            for key, value in kwargs.items():
                setattr(entry, key, value)
            session.commit()
            return True
        return False

    @session_manager
    def delete_table_prompt(self, key_id, session=None):
        if entry := self.query_data_by_id(key_id):
            session.delete(entry)
            session.commit()
            return True
        return False


if __name__ == "__main__":
    if __name__ == "__main__":
        # 测试
        to_srt_orm = PromptsOrm()
        # to_srt_orm.add_data_to_table(prompt_name="默认", prompt_content="test2")
        one_srt = to_srt_orm.query_data_by_id(1)
        lang = 'zh-CN'
        # print(one_srt.prompt_content)

        # 替换 {lang} 为 zh-cn
        modified_content = one_srt.prompt_content.format(lang='zh-cn',text='你好')
        print(modified_content)

        # all_srt = to_srt_orm.get_all_data()  # print(all_srt)  # for srt in all_srt:  #     print(srt)
