from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker

from orm.inint import engine, ToSrt, ToTranslation, Prompts

# 创建一个数据库会话
Session = sessionmaker(bind=engine)
session = Session()


class ToSrtOrm:
    # 添加ToSrt数据

    def add_data_to_table(self, unid, path, source_language, source_module_status, source_module_name, translate_status, cuda, raw_ext, job_status=0, obj=None, ):
        if obj is None:
            obj = {}
        new_entry = ToSrt(unid=unid, path=path, source_language=source_language, source_module_status=source_module_status, source_module_name=source_module_name, translate_status=translate_status, cuda=cuda,
            raw_ext=raw_ext, job_status=job_status, obj=obj, )
        session.add(new_entry)
        session.commit()

    def get_all_data(self):
        return session.query(ToSrt).all()

    def query_data_by_unid(self, unid):
        try:
            return session.query(ToSrt).filter_by(unid=unid).one()
        except NoResultFound:
            return None

    def query_data_all(self):
        return session.query(ToSrt).all()

    def query_data_format_unid_path(self):
        # 输出所有行的unid和path
        return session.query(ToSrt.unid, ToSrt.path, ToSrt.job_status).all()

    def update_table_unid(self, unid, **kwargs):
        if entry := self.query_data_by_unid(unid):
            for key, value in kwargs.items():
                setattr(entry, key, value)
            session.commit()
            return True
        return False

    def delete_table_unid(self, unid):
        if entry := self.query_data_by_unid(unid):
            session.delete(entry)
            session.commit()
            return True
        return False

    def close_session(self):
        session.close()


# 添加


class ToTranslationOrm:
    # 添加ToTranslation数据
    def add_to_translation(self, unid, path, source_language, target_language, translate_type):
        new_entry = ToTranslation(unid=unid, path=path, source_language=source_language, target_language=target_language, translate_type=translate_type, )
        session.add(new_entry)
        session.commit()

    def get_all_to_translation(self):
        return session.query(ToTranslation).all()

    def get_to_translation_by_unid(self, unid):
        try:
            return session.query(ToTranslation).filter_by(unid=unid).one()
        except NoResultFound:
            return None

    def update_to_translation(self, unid, **kwargs):
        if entry := self.get_to_translation_by_unid(unid):
            for key, value in kwargs.items():
                setattr(entry, key, value)
            session.commit()
            return True
        return False

    def delete_to_translation(self, unid):
        if entry := self.get_to_translation_by_unid(unid):
            session.delete(entry)
            session.commit()
            return True
        return False

    def close_session(self):
        session.close()


class PromptsOrm:
    def add_data_to_table(self, prompt):
        new_entry = Prompts(prompt=prompt)
        session.add(new_entry)
        session.commit()

    def get_all_data(self):
        return session.query(Prompts).all()
    
    def query_data_by_prompt(self, prompt):
        try:
            return session.query(Prompts).filter_by(prompt=prompt).one()
        except NoResultFound:
            return None

    def update_table_prompt(self, prompt, **kwargs):
        if entry := self.query_data_by_prompt(prompt):
            for key, value in kwargs.items():
                setattr(entry, key, value)
            session.commit()
            return True
        return False

    def delete_table_prompt(self, prompt):
        if entry := self.query_data_by_prompt(prompt):
            session.delete(entry)
            session.commit()
            return True
        return False

    def close_session(self):
        session.close()
            


if __name__ == "__main__":
    # 测试
    to_srt_orm = ToSrtOrm()
    all_srt = to_srt_orm.query_data_format_unid_path()
    # print(all_srt)
    for srt in all_srt:
        print(srt)
