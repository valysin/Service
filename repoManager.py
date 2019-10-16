#coding:utf-8
import configparser
import json
import time
from threading import Thread

import requests
from service.RepositoryService import RepositoryService
import uuid as UUID
from kafka import KafkaProducer
from kafka import KafkaConsumer
import traceback
from db.model import RepositoryModel
from config import config
import re

GIT_API_URL_PREFIX = config.GIT_API_URL_PREFIX
GITLAB_TOKEN = config.GITLAB_TOKEN
GITHUB_TOKEN = config.GITHUB_TOKEN
API_HEADER = {
    'github': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0',
               'Authorization': 'token ' + GITHUB_TOKEN},
    'gitlab': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0',
               'Private-Token': GITLAB_TOKEN},
}
LOCAL_ADDR_PREFIX = config.LOCAL_ADDR_PREFIX
REPO_ROOT_PATH_PATTERN = config.REPO_ROOT_PATH_PATTERN
KAFKA_HOST = config.KAFKA_HOST['host-1']
KAFKA_GROUP_ID = config.KAFKA_GROUP_ID

KAFKA_TOPIC_1 = config.KAFKA_TOPIC['RepoManager']
KAFKA_TOPIC_2 = config.KAFKA_TOPIC['ProjectManager']
KAFKA_TOPIC_3 = config.KAFKA_TOPIC['CompleteDownload']
KAFKA_TOPIC_6 = config.KAFKA_TOPIC['DuplicateRepo']


class RepositoryHandler(Thread):

    def __init__(self, repository_service):
        super().__init__()
        self.repository_service = repository_service

    def run(self):
        try:
            self.repository_service.add_repository()
            # repository.copy()
        except Exception as e:
            log(e.__str__())
            traceback.print_exc()
            send_failed_msg(project_id)
            if e.__str__() != '项目下载失败':
                try:
                    self.repository_service.delete()
                    self.repository_service.remove_repository()
                except Exception as e:
                    log(e.__str__())

        else:
            try:
                download_message = {'repoId': repository_service.repository.uuid, 'local_addr': repository.local_addr, 'max_index': 0,
                                    'flag': 'first added and not existed'}
                send_msg(host=KAFKA_HOST, recv=KAFKA_TOPIC_3, msg=download_message)
                repo_message = {
                    'projectId': project_id,
                    'language': repository_service.repository.language,
                    'VCS-Type': 'git',
                    'status': 'Downloaded',
                    'description': repository_service.repository.description,
                    'repoId': repository_service.repository.uuid
                }
                send_msg(host=KAFKA_HOST, recv=KAFKA_TOPIC_1, msg=repo_message)
                self.repository_service.repository.copy()

            except Exception as e:
                log(e.__str__())
                traceback.print_exc()



def get_project_info(addr):
    flag = 0
    while True:
        try:# https://api.github.com/repos/
            url = GIT_API_URL_PREFIX + '/' + addr
            TYPE = config.REPO_TYPE
            response = requests.get(url, timeout=15, headers=API_HEADER[TYPE])
            if response.status_code != 200:
                return None
            json_data = response.json()
        except Exception as e:
            log(e.__str__())
            traceback.print_exc()
            flag += 1
            if flag > 3:
                return None
        else:
            if 'message' in json_data or 'id' not in json_data:
                return None
            return json_data


def log(string):
    t = time.strftime(r"%Y-%m-%d-%H:%M:%S", time.localtime())
    print("[%s]%s" % (t, string))


def send_failed_msg(project_id):
    producer = KafkaProducer(bootstrap_servers=KAFKA_HOST, api_version=(0, 9))
    new_msg = {
        'projectId': project_id,
        'language': 'null',
        'VCS-Type': 'null',
        'status': 'failed',
        'description': 'null'
    }
    producer.send(KAFKA_TOPIC_1, json.dumps(new_msg).encode())
    producer.close()


def send_msg(host, recv, msg):
    producer = KafkaProducer(bootstrap_servers=host, api_version=(0, 9))
    producer.send(recv, json.dumps(msg).encode())
    producer.close()

if __name__ == '__main__':

    log('start consumer')
    consumer = KafkaConsumer(KAFKA_TOPIC_2,
                             bootstrap_servers=[KAFKA_HOST],
                             group_id=KAFKA_GROUP_ID,
                             )
    consumer.poll()

    for msg in consumer:
        try:
            recv = "%s:%d:%d: key=%s value=%s" % (msg.topic, msg.partition, msg.offset, msg.key, msg.value)
            log(recv)
            json_data = json.loads(msg.value.decode())
        except Exception as e:
            log(e.__str__())
            traceback.print_exc()
        else:
            url = json_data['url']
            project_id = json_data['projectId']
            username = None
            password = None
            branch = json_data['branch']
            if json_data['private'] is True:
                username = json_data['username']
                password = json_data['password']
                project_info = {
                    'id': None,
                    'language': 'Java',
                    'description': None,
                }
            else:
                addr = re.findall(REPO_ROOT_PATH_PATTERN, url)[0]
                # assert isinstance(addr, str) and addr != ''
                local_addr = addr + '-' + branch
                project_info = get_project_info(addr)

            if project_info is None:
                send_failed_msg(project_id)
            else:
                repository = RepositoryModel(repository_id = int(project_info.get('id')),
                                             language = project_info.get('language'),
                                             uuid = UUID.uuid1().__str__(),
                                             url = url,
                                             description = project_info.get('description'),
                                             is_private = json_data['private'],
                                             local_addr = local_addr,
                                             branch = branch)
                repository_service = RepositoryService(repository, username, password)
                if not repository_service.is_existed():
                    handler = RepositoryHandler(repository_service)
                    handler.start()
                else:  # 密码是否正确
                    try:
                        repository.uuid = repository_service.get_uuid_by_addr()
                    except Exception as e:
                        log(e.__str__())
                        traceback.print_exc()
                        send_failed_msg(project_id)
                    else:
                        try:
                            download_message = {'repoId': repository.uuid, 'local_addr': repository.local_addr,
                                                'max_index': 0, 'flag': 'first added and existed'}
                            send_msg(host=KAFKA_HOST, recv=KAFKA_TOPIC_3, msg=download_message)
                            repo_message = {
                                'projectId': project_id,
                                'language': repository.language,
                                'VCS-Type': 'git',
                                'status': 'Downloaded',
                                'description': repository.description,
                                'repoId': repository.uuid
                            }
                            send_msg(host=KAFKA_HOST, recv=KAFKA_TOPIC_1, msg=repo_message)
                        except Exception as e:
                            log(e.__str__())
                            traceback.print_exc()
