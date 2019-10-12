from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.dialects.mysql import TEXT, MEDIUMTEXT
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class RepositoryModel(Base):
    __tablename__ = 'repository'

    repository_id = Column(Integer)
    uuid = Column(String(36), primary_key=True)
    language = Column(String(255))
    url = Column(String(512))
    description = Column(TEXT)
    is_private = Column(Boolean)
    local_addr = Column(String(512))
    branch = Column(String(255))

class CommitModel(Base):
    __tablename__ = 'commit'

    uuid = Column(String(36), primary_key=True)
    commit_id = Column(String(64))
    message = Column(MEDIUMTEXT)
    developer = Column(String(64))
    commit_time = Column(DateTime)
    repo_id = Column(String(36))
    developer_email = Column(String(255))
    self_index = Column(Integer)


if __name__ == '__main__':
    Base.metadata.create_all()