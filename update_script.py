#coding:utf-8

import configparser
import json

import MysqlOperation
import os
from kafka import KafkaProducer

config = configparser.ConfigParser()
config.read('config.conf')

KAFKA_HOST = config.get('KafkaHost', 'host-1')

REPO_PATH = config.get('Path', 'path')
# KAFKA_TOPIC_SCAN = config.get('KafkaTopic', 'scan')     # config中加入新配置

result = MysqlOperation.get_data_from_mysql(
    tablename='repository',
    fields=['uuid', 'local_addr']
)

commit_list = []

# 现有数据库上填充self_index：
# 建立commit_sha到self_index的映射
# 打开对应repo的commit_log文件 建立commit_sha和self_index的映射
# 一条一条update

for item in result:
    os.chdir(REPO_PATH + '/' + item[1])
    os.system('git log --pretty=format:"%H" > check.log')
    sha2index = {}
    with open(REPO_PATH + '/' + item[1] + '/check.log', 'r', encoding='UTF-8') as f:
        length = f.readlines().__len__()
    with open(REPO_PATH + '/' + item[1] + '/check.log', 'r', encoding='UTF-8') as f:
        index = 0
        for line in f.readlines():
            sha2index[line[:-1]] = length - index
            index += 1

        for key, value in sha2index.items():
            MysqlOperation.update_mysql(
                tablename = 'commit',
                params = {
                    'commit_id':key,
                    'self_index':value
                },
                pk = 'commit_id'
            )
