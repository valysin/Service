import configparser
import json
import os
import sys
import traceback
from threading import Thread

sys.path.append("..")


from kafka import KafkaConsumer
from redis import Redis
from repoManager import Repository
from repoManager import send_msg
from repoManager import send_failed_msg
from repoManager import log

class DuplicateRepository(Repository, Thread):

    def __init__(self, info, url, url_type, is_private, branch, repo_id, username=None, password=None):
        self.username = username
        self.password = password
        super().__init__(info, url, url_type, is_private, branch, repo_id)

    def copy(self, username=None, password=None):
        r = Redis(host=REDIS_HOST, db=REDIS_DB, password=REDIS_PASSWORD)
        for i in range(3):
            os.chdir(REPO_PATH + '/' + self.root_path)
            ret = os.system('cp -r %s %s' % (self.repo_name, self.repo_name + '_duplicate_fdse-' + str(i)))
            if ret != 0:
                raise Exception
            else:
                r.lpush(self.uuid, "%s-%s-%s" % (LOCALHOST, self.branch, str(i)))
        # r.lpush(self.uuid, 'none')

        # 发送给其他服务器 进行备份

    #     UUID 要传过来 这里UUID会自动生成

    def run(self):
        try:
            self.download(self.username, self.password)
            self.copy(self.username, self.password)
        except Exception as e:
            traceback.print_exc()
            log(e.__str__())


KAFKA_TOPIC_6 = 'DuplicateRepo'
MAX_POLL_RECORDS = 10

if __name__ == '__main__':

    config = configparser.ConfigParser()
    config.read('../config.conf')
    REPO_PATH = config.get('Path', 'path')
    REDIS_HOST = config.get('redis', 'host')
    REDIS_DB = config.get('redis', 'db')
    REDIS_PASSWORD = config.get('redis', 'password')
    LOCALHOST = config.get('localhost', 'host')
    KAFKA_HOST = config.get('KafkaHost', 'host-1')
    KAFKA_GROUP_ID = config.get('KafkaGroup', 'id-1')



    log('start consumer')
    consumer = KafkaConsumer(KAFKA_TOPIC_6,
                             bootstrap_servers=[KAFKA_HOST],
                             group_id=KAFKA_GROUP_ID)
    # consumer.poll(MAX_POLL_RECORDS)
    # consumer.seek_to_end()

    for msg in consumer:
        try:
            recv = "%s:%d:%d: key=%s value=%s" % (msg.topic, msg.partition, msg.offset, msg.key, msg.value)
            log(recv)
            json_data = json.loads(msg.value.decode())

        except Exception as e:
            log(e.__str__())
            traceback.print_exc()

        else:
            try:
                info = json_data['info']
                url = json_data['url']
                url_type = json_data['url_type']
                is_private = json_data['is_private']
                branch = json_data['branch']
                username = json_data['username']
                password = json_data['password']
                repo_id = json_data['repo_id']
                duplicate = DuplicateRepository(info, url, url_type, is_private, branch, repo_id, username, password)
                duplicate.run()
            except Exception as e:
                log(e.__str__())
                traceback.print_exc()