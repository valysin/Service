from apscheduler.schedulers.blocking import BlockingScheduler
from config import config
import logging

schedule = BlockingScheduler()

logger = logging.getLogger()
fh = logging.FileHandler('./log/bufferManager.log', mode='w')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] : %(message)s', '%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
logger.addHandler(fh)

REDIS = config.REDIS
DB = config.ISSUE_TRACKER_MYSQL_DB
HOST = config.LOCALHOST

def release_sources():
    from redis import Redis
    r = Redis(host=REDIS['host'],password= REDIS['password'], db=REDIS['db'])

    from libs.tool import db_connect
    from db.model import RepositoryModel
    logger.debug('Start releasing ...')
    session = db_connect(DB)
    logger.debug('Database has been connected')
    query = session.query(RepositoryModel.uuid, RepositoryModel.branch).filter().all()
    session.close()
    # repository表添加branch字段
    s = set()
    for item in query:
        key_length = r.llen(item.uuid)
        for value in r.lrange(item.uuid, 0, key_length - 1):
            s.add(value)
        if s.__len__() < key_length: # 释放出现问题,重复none或重复键值
            for index in range(key_length):
                if index == 0:
                    r.lpush(item.uuid, 'none')
                    r.rpop(item.uuid)
                else:
                    r.lpush(item.uuid, "%s-%s-%s" % (HOST, item.branch, index - 1))
                    r.rpop(item.uuid)
        s.clear()
    logger.debug('Releasing has been finished !')


schedule.add_job(release_sources, 'cron', hour=6)
schedule.start()