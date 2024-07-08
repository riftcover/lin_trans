from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker

from orm.inint import engine, ToSrt, ToTranslation

# 创建一个数据库会话
Session = sessionmaker(bind=engine)
session = Session()


class ToSrtOrm:
    # 添加ToSrt数据
    def add_to_srt(self, unid, path,
                   source_language, source_module_status, source_module_name,
                   translate_status, cuda, raw_ext,job_status=0):

        new_entry = ToSrt(unid=unid, path=path,
                          source_language=source_language, source_module_status=source_module_status, source_module_name=source_module_name,
                          translate_status=translate_status, cuda=cuda, raw_ext=raw_ext,job_status=job_status)
        session.add(new_entry)
        session.commit()

    def get_all_to_srt(self):
        return session.query(ToSrt).all()

    def get_to_srt_by_unid(self, unid):
        try:
            return session.query(ToSrt).filter_by(unid=unid).one()
        except NoResultFound:
            return None

    def get_to_srt_all(self):
        return session.query(ToSrt).all()

    def get_all_format_unid_path(self):
        # 输出所有行的unid和path
        return session.query(ToSrt.unid, ToSrt.path,ToSrt.job_status).all()

    def update_to_srt(self, unid, **kwargs):
        entry = self.get_to_srt_by_unid(unid)
        if entry:
            for key, value in kwargs.items():
                setattr(entry, key, value)
            session.commit()
            return True
        return False

    def delete_to_srt(self, unid):
        entry = self.get_to_srt_by_unid(unid)
        if entry:
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
        new_entry = ToTranslation(unid=unid, path=path, source_language=source_language, target_language=target_language, translate_type=translate_type)
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
        entry = self.get_to_translation_by_unid(unid)
        if entry:
            for key, value in kwargs.items():
                setattr(entry, key, value)
            session.commit()
            return True
        return False

    def delete_to_translation(self, unid):
        entry = self.get_to_translation_by_unid(unid)
        if entry:
            session.delete(entry)
            session.commit()
            return True
        return False

    def close_session(self):
        session.close()


if __name__ == '__main__':
    # 测试
    to_srt_orm = ToSrtOrm()
    all_srt = to_srt_orm.get_all_format_unid_path()
    # print(all_srt)
    for srt in all_srt:
        print(srt)