#coding:utf-8

import configparser
import json

import MysqlOperation
import os
from kafka import KafkaProducer
import time

config = configparser.ConfigParser()
config.read('config.conf')

KAFKA_HOST = config.get('KafkaHost', 'host-1')

REPO_PATH = config.get('Path', 'path')
KAFKA_TOPIC_COMPLETE_DOWNLOAD = config.get('KafkaTopic', 'topic-3')     # config中加入新配置

def log(string):
    t = time.strftime(r"%Y-%m-%d-%H:%M:%S", time.localtime())
    print("[%s]%s" % (t, string))


while True:
    try:
        result = MysqlOperation.get_data_from_mysql(
            tablename='repository',
            fields=['uuid', 'local_addr']
        )

        commit_list = []
    except Exception as e:
        log(e.__str__())
        time.sleep(3 * 3600)

    else:
        for item in result:
            try:
                uuid = item[0]
                branch = item[1].split('-')[-1]
                split = item[1].split('/')
                user = split[1]
                repo_type = split[0]
                repo_name = split[-1]
                os.chdir(REPO_PATH + '/' + item[1])
                os.system('git checkout %s' % branch)
                os.system('git pull')
                os.system('git log --pretty=format:"%H" > check.log')
                with open(REPO_PATH + '/' + item[1] + '/check.log', 'r', encoding='UTF-8') as f:
                    length = f.readlines().__len__()

                max_index = MysqlOperation.get_data_from_mysql(
                    sql='select max(self_index) from commit where repo_id = "%s"' % uuid
                )[0][0]

                if length > max_index:
                    producer = KafkaProducer(bootstrap_servers=KAFKA_HOST, api_version=(0, 9))
                    msg = {
                        'repoId': uuid,
                        'local_addr':item[1],
                        'max_index':max_index,
                        'flag':'not first added and existed'
                    }
                    producer.send(KAFKA_TOPIC_COMPLETE_DOWNLOAD, json.dumps(msg).encode())
                    producer.close()

                for i in range(3):
                    # 项目备份名:<repo_name>_duplicate_fdse-<index>
                    os.chdir(REPO_PATH + '/%s/%s/%s_duplicate_fdse-%s' % (repo_type, user, repo_name, str(i))) # 之后要加入分支名
                    os.system('git checkout %s' % branch)
                    os.system('git pull')

            except Exception as e:
                log(e.__str__())

    time.sleep(2 * 3600)