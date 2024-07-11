from functools import wraps

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker, scoped_session

from orm.inint import Prompts, engine

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


# class ToSrtOrm:
#     # 添加ToSrt数据
#
#     @session_manager
#     def add_data_to_table(self, unid, path, source_language, source_module_status, source_module_name, translate_status, cuda, raw_ext, job_status=0, obj=None, ):
#         if obj is None:
#             obj = {}
#         new_entry = ToSrt(unid=unid, path=path, source_language=source_language, source_module_status=source_module_status, source_module_name=source_module_name, translate_status=translate_status, cuda=cuda,
#             raw_ext=raw_ext, job_status=job_status, obj=obj, )
#         session.add(new_entry)
#         session.commit()
#
#     def get_all_data(self):
#         return session.query(ToSrt).all()
#
#     def query_data_by_unid(self, unid):
#         try:
#             return session.query(ToSrt).filter_by(unid=unid).one()
#         except NoResultFound:
#             return None
#
#     def query_data_all(self):
#         return session.query(ToSrt).all()
#
#     def query_data_format_unid_path(self):
#         # 输出所有行的unid和path
#         return session.query(ToSrt.unid, ToSrt.path, ToSrt.job_status).all()
#
#     def update_table_unid(self, unid, **kwargs):
#         if entry := self.query_data_by_unid(unid):
#             for key, value in kwargs.items():
#                 setattr(entry, key, value)
#             session.commit()
#             return True
#         return False
#
#     def delete_table_unid(self, unid):
#         if entry := self.query_data_by_unid(unid):
#             session.delete(entry)
#             session.commit()
#             return True
#         return False
#
#     def close_session(self):
#         session.close()
#
#
# # 添加
#
#
# class ToTranslationOrm:
#     # 添加ToTranslation数据
#     def add_to_translation(self, unid, path, source_language, target_language, translate_type):
#         new_entry = ToTranslation(unid=unid, path=path, source_language=source_language, target_language=target_language, translate_type=translate_type, )
#         session.add(new_entry)
#         session.commit()
#
#     def get_all_to_translation(self):
#         return session.query(ToTranslation).all()
#
#     def get_to_translation_by_unid(self, unid):
#         try:
#             return session.query(ToTranslation).filter_by(unid=unid).one()
#         except NoResultFound:
#             return None
#
#     def update_to_translation(self, unid, **kwargs):
#         if entry := self.get_to_translation_by_unid(unid):
#             for key, value in kwargs.items():
#                 setattr(entry, key, value)
#             session.commit()
#             return True
#         return False
#
#     def delete_to_translation(self, unid):
#         if entry := self.get_to_translation_by_unid(unid):
#             session.delete(entry)
#             session.commit()
#             return True
#         return False
#
#     def close_session(self):
#         session.close()


class PromptsOrm:
    @session_manager
    def add_data_to_table(self,prompt_name: str, prompt_content: str,session=None):
        new_entry = Prompts(prompt_name=prompt_name,prompt_content=prompt_content)
        session.add(new_entry)
        session.commit()

    @session_manager
    def get_all_data(self,session=None):
        prompts = session.query(Prompts).all()
        # 确保所有相关的属性都被加载
        # 要返回主键id，得改成dict？？ 试一下原生的有id回来么
        result = []
        for prompt in prompts:
            session.refresh(prompt)
            result.append({'id': prompt.id, 'prompt_name': prompt.prompt_name, 'prompt_content': prompt.prompt_content})
        session.expunge_all()
        return result

    @session_manager
    def query_data_by_prompt(self, key_id: int,session=None):
        # 输入prompt_name查询数据
        try:
            prompt = session.query(Prompts).filter_by(id=key_id).one()
            session.refresh(prompt)
            result = {'id': prompt.id, 'prompt_name': prompt.prompt_name, 'prompt_content': prompt.prompt_content}
            session.expunge(prompt)
            return result
        except NoResultFound:
            return None

    @session_manager
    def update_table_prompt(self, key_id: int,session=None, **kwargs,):
        if entry := self.query_data_by_prompt(key_id):
            for key, value in kwargs.items():
                setattr(entry, key, value)
            session.commit()
            return True
        return False

    @session_manager
    def delete_table_prompt(self, key_id,session=None):
        if entry := self.query_data_by_prompt(key_id):
            session.delete(entry)
            session.commit()
            return True
        return False

            


if __name__ == "__main__":
    # 测试
    to_srt_orm = PromptsOrm()
    # to_srt_orm.add_data_to_table(prompt_name="test1", prompt_content="test1")
    all_srt = to_srt_orm.get_all_data()
    print(all_srt)
    # for srt in all_srt:
    #     print(srt)
