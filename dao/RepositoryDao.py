from config import config
from db.model import RepositoryModel


class RepositoryDao:

    def __init__(self, repository):
        self.repository = repository


    def insert(self):
        from libs.tool import db_connect
        DB = config.ISSUE_TRACKER_MYSQL_DB
        session = db_connect(DB)
        session.add(self.repository)
        session.commit()
        session.close()

    def get_uuid_by_local_addr(self):
        from libs.tool import db_connect
        DB = config.ISSUE_TRACKER_MYSQL_DB
        session = db_connect(DB)
        ret = session.query(RepositoryModel.uuid).filter(RepositoryModel.local_addr == self.repository.local_addr).first()
        session.close()
        return ret

    def delete(self):
        from libs.tool import db_connect
        DB = config.ISSUE_TRACKER_MYSQL_DB
        session = db_connect(DB)
        session.delete(self.repository)
        session.commit()
        session.close()