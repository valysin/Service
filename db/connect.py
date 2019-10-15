from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import create_engine  # 导入engine
from config import config

def connect(host, port, username, password):
    HOST = config.ISSUE_TRACKER_MYSQL_DB['host']
    PORT = config.ISSUE_TRACKER_MYSQL_DB['port']
    DATABASE = config.ISSUE_TRACKER_MYSQL_DB['db']
    USERNAME = config.ISSUE_TRACKER_MYSQL_DB['user']
    PASSWORD = config.ISSUE_TRACKER_MYSQL_DB['passwd']

    # 构造一个url
    db_url = 'mysql+mysqlconnector://%s:%s@%s:%s/%s?charset=utf8mb4' % (
        USERNAME,
        PASSWORD,
        HOST,
        PORT,
        DATABASE
    )

    engine = create_engine(db_url)

    return engine