# coding:utf-8

import json
import MysqlOperation
from kafka import KafkaConsumer, KafkaProducer
import configparser
import uuid
from datetime import datetime
import pytz
import time


def local_to_utc(time_str, utc_format='%a %b %d %H:%M:%S %Y %z'):
    if int(time_str[-5:]) // 100 >= 0 :
        timezone = pytz.timezone('Etc/GMT' + str(-int(time_str[-5:]) // 100))
    else:
        timezone = pytz.timezone('Etc/GMT+' + str(-int(time_str[-5:]) // 100))
    local_format = "%Y-%m-%d %H:%M:%S"
    utc_dt = datetime.strptime(time_str, utc_format)
    local_dt = utc_dt.replace(tzinfo=timezone).astimezone(pytz.utc)
    return local_dt.strftime(local_format)

def log(string):
    t = time.strftime(r"%Y-%m-%d-%H:%M:%S", time.localtime())
    print("[%s]%s" % (t, string))

def create_commit_log(path):
    import os
    os.chdir(path)
    os.system('git log --pretty=format:"%H|++*淦*++|%an|++*淦*++|%ad|++*淦*++|%ae|++*淦*++|%s" > commit_log.log')


def get_commit_info(path, max_index):
    with open(path, 'r', encoding='UTF-8') as f:
        length = f.readlines().__len__()

    with open(path, 'r', encoding='UTF-8') as f:
        commit_list = []
        uuids = []
        commit_sha = []
        developer = []
        commit_time = []
        developer_email = []
        message = []
        self_index = []

        for line in f.readlines():
            commit_list.append(line.split('|++*淦*++|'))

        for index in range(0, length - max_index):
            uuids.append(uuid.uuid1().__str__())
            self_index.append(length - index)
            commit_sha.append(commit_list[index][0])
            developer.append(commit_list[index][1])
            commit_time.append(local_to_utc(commit_list[index][2]))
            developer_email.append(commit_list[index][3])
            message.append(commit_list[index][4])

        dic = dict()
        dic['uuids'] = uuids
        dic['message'] = message
        dic['commit_id'] = commit_sha
        dic['commit_time'] = commit_time
        dic['developer_email'] = developer_email
        dic['developer'] = developer
        dic['self_index'] = self_index

        return dic

config = configparser.ConfigParser()
config.read('config.conf')
REPO_PATH = config.get('Path', 'path')
KAFKA_HOST = config.get('KafkaHost', 'host-1')
KAFKA_TOPIC_COMPLETE_DOWNLOAD = config.get('KafkaTopic', 'topic-3')
KAFKA_TOPIC_SCAN = config.get('KafkaTopic', 'topic-4')
KAFKA_TOPIC_UPDATE_COMMIT = config.get('KafkaTopic', 'topic-5')


consumer = KafkaConsumer(KAFKA_TOPIC_COMPLETE_DOWNLOAD,
                         bootstrap_servers=[KAFKA_HOST],
                         api_version=(0, 9),
                         max_poll_records=10)

for msg in consumer:
    recv = "%s:%d:%d: key=%s value=%s" % (msg.topic, msg.partition, msg.offset, msg.key, msg.value)
    log(recv)
    msg_list = []


    json_data = json.loads(msg.value.decode())
    repo_id = json_data['repoId']
    local_addr = json_data['local_addr']
    max_index = json_data['max_index']
    flag = json_data['flag']
    producer = KafkaProducer(bootstrap_servers=KAFKA_HOST, api_version=(0, 9))

    if flag == 'first added and not existed' or flag == 'not first added and existed':
        new_path = REPO_PATH + '/' + local_addr
        create_commit_log(new_path)
        commit_info = get_commit_info(new_path + '/commit_log.log', max_index)
        MysqlOperation.insert_into_mysql(
            tablename='commit',
            params={
                'uuid':commit_info['uuids'],
                'commit_id':commit_info['commit_id'],
                'message':commit_info['message'],
                'commit_time':commit_info['commit_time'],
                'repo_id':[repo_id] * len(commit_info['uuids']),
                'developer':commit_info['developer'],
                'developer_email':commit_info['developer_email'],
                'self_index':commit_info['self_index']
            },
            mode='multiple'
        )

        if flag == 'not first added and existed':
            for index in range(0, len(commit_info['commit_id'])):
                msg = {
                    'repoId': repo_id,
                    'commitId': commit_info['commit_id'][len(commit_info['commit_id']) - index - 1],
                    'category': 'bug'
                }
                producer.send(KAFKA_TOPIC_SCAN, json.dumps(msg).encode())
                log(str(msg))
            producer.close()
            commit_info.clear()

        if flag == 'first added and not existed':
            for commit_id, commit_time in zip(commit_info['commit_id'], commit_info['commit_time']):
                msg = {
                    'repoId': repo_id,
                    'commitId': commit_id,
                    'commitTime': commit_time,
                }
                msg_list.append(msg)
            msg_list.sort(key=lambda x: x['commitTime'])
            end = 0
            while end is not None:
                start = end
                end = end + 300 if end + 300 < len(msg_list) else None
                producer.send(KAFKA_TOPIC_UPDATE_COMMIT, json.dumps(msg_list[start:end]).encode())
            log(str(msg_list))
            producer.close()
            msg_list.clear()
            commit_info.clear()

    else:
        ret = MysqlOperation.get_data_from_mysql(
            tablename='commit',
            params={'repo_id':repo_id},
            fields=['commit_id', 'commit_time']
        )
        for item in ret:
            msg = {
                'repoId': repo_id,
                'commitId': item[0],
                'commitTime': item[1].__str__(),
            }
            msg_list.append(msg)
        msg_list.sort(key=lambda x: x['commitTime'])
        end = 0
        while end is not None:
            start = end
            end = end + 300 if end + 300 < len(msg_list) else None
            producer.send(KAFKA_TOPIC_UPDATE_COMMIT, json.dumps(msg_list[start:end]).encode())
            log(str(msg_list))
        producer.close()
        msg_list.clear()

#    发给scan
# project repository commit