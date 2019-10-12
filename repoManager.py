#coding:utf-8
import configparser
import json
import time
from threading import Thread

import requests
import os
import MysqlOperation
import uuid
from kafka import KafkaProducer
from kafka import KafkaConsumer
import traceback
from redis import Redis

config = configparser.ConfigParser()
config.read('config.conf')

REPO_PATH = config.get('Path', 'path')

KAFKA_HOST = config.get('KafkaHost', 'host-1')
LOCALHOST = config.get('localhost', 'host')
KAFKA_TOPIC_1 = config.get('KafkaTopic', 'topic-1')
KAFKA_TOPIC_2 = config.get('KafkaTopic', 'topic-2')
KAFKA_TOPIC_3 = config.get('KafkaTopic', 'topic-3')
KAFKA_TOPIC_6 = config.get('KafkaTopic', 'topic-6')

KAFKA_GROUP_ID = config.get('KafkaGroup', 'id-1')

MAX_POLL_RECORDS = int(config.get('Kafka', 'max_poll_records'))

GITHUB_TOKEN = config.get('github', 'token-1')
GITLAB_TOKEN = config.get('gitlab', 'token-1')

API_HEADER = {
    'gitlab': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0',
               'Private-Token': GITLAB_TOKEN},
    'github': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0',
               'Authorization': 'token ' + GITHUB_TOKEN}
}

REDIS_HOST = config.get('redis', 'host')
REDIS_DB = config.get('redis', 'db')
REDIS_PASSWORD = config.get('redis', 'password')

class UrlError(Exception):
    def __init__(self, ErrorInfo):
        super().__init__(self)
        self.error_info = ErrorInfo

    def __str__(self):
        return self.error_info


class DownloadError(Exception):
    def __init__(self, ErrorInfo):
        super().__init__(self)
        self.error_info = ErrorInfo

    def __str__(self):
        return self.error_info


class RepositoryHandler(Thread):

    def __init__(self, repository, username, password):
        super().__init__()
        self.repository = repository
        self.username = username
        self.password = password

    def run(self):
        try:
            self.repository.download(self.username, self.password)
            self.repository.insert_into_db()
            # repository.copy()

        except Exception as e:
            log(e.__str__())
            traceback.print_exc()
            send_failed_msg(project_id)
            self.repository.delete_repo()
            self.repository.delete_from_db()

        else:
            try:
                download_message = {'repoId': repository.uuid, 'local_addr': repository.rel_path, 'max_index': 0,
                                    'flag': 'first added and not existed'}
                send_msg(host=KAFKA_HOST, recv=KAFKA_TOPIC_3, msg=download_message)
                repo_message = {
                    'projectId': project_id,
                    'language': repository.language,
                    'VCS-Type': repository.vcs_type,
                    'status': 'Downloaded',
                    'description': repository.description,
                    'repoId': repository.uuid
                }
                send_msg(host=KAFKA_HOST, recv=KAFKA_TOPIC_1, msg=repo_message)
                self.repository.copy(self.username, self.password)

            except Exception as e:
                log(e.__str__())
                traceback.print_exc()


class Repository:

    def __init__(self, info, url, url_type, is_private, branch, repo_id=None):
        self.info = info
        self.url = url
        self.url_type = url_type
        self.is_private = is_private
        self.branch = branch

        self.vcs_type = get_vcs_type(self.url)
        self.description = '' if self.info['description'] is None else self.info['description']
        self.language = '' if self.info['language'] is None else self.info['language']
        self.repository_id = self.info['id']

        split = self.url.split('/')
        self.repo_path_prefix = '/'.join(split[3:-1])  # 取得项目根路径的父路径 https://github.com/a/b/c → a/b
        self.repo_name = split[-1] + '-' + branch.replace(' ', '_').replace('/', '-')

        self.uuid = repo_id if repo_id is not None else uuid.uuid1().__str__()

        self.rel_path = '/'.join([url_type, self.repo_path_prefix, self.repo_name])
        self.root_path = '/'.join([url_type, self.repo_path_prefix])

    def set_uuid(self):
        self.uuid = uuid.uuid1().__str__()

    def is_valid(self):
        flag = 0
        while True:
            try:
                response = requests.get(self.url, timeout=15).headers['Status']
            except Exception as e:
                flag += 1
                if flag > 3:
                    return False
            else:
                if '200' in response:
                    return True
                else:
                    return False

    def is_in_db(self):
        try:
            result = MysqlOperation.get_data_from_mysql(
                tablename='repository',
                params={'local_addr': self.rel_path},
                fields=['uuid']
            )
        except Exception as e:
            raise e
        else:
            if len(result) == 0:
                return False
            else:
                return True

    def is_repo_existed(self):
        return os.path.exists(REPO_PATH + '/' + self.rel_path)

    def copy(self, username=None, password=None):

        r = Redis(host=REDIS_HOST, db=REDIS_DB, password=REDIS_PASSWORD)

        for i in range(3):
            os.chdir(REPO_PATH + '/' + self.root_path)
            ret = os.system('cp -r %s %s' % (self.repo_name, self.repo_name + '_duplicate_fdse-' + str(i)))
            # 备份文件名：<repo_name>_duplicate_fdse-<index>  repo_name: <repo>-<branch>
            if ret != 0:
                raise Exception
            else:
                r.lpush(self.uuid, "%s-%s-%s" % (LOCALHOST, self.branch, str(i)))
        # 发送给其他服务器 进行备份
        r.rpush(self.uuid, 'none')
        copy_message = {
            'url': self.url,
            'info': self.info,
            'branch': self.branch,
            'url_type': self.url_type,
            'username': username,
            'password': password,
            'is_private': self.is_private,
            'repo_id': self.uuid
        }
        send_msg(host=KAFKA_HOST, recv=KAFKA_TOPIC_6, msg=copy_message)


    def download(self, username=None, password=None):
        # 暂时只适用于github的标准url
        if not os.path.exists(REPO_PATH + '/' + self.root_path):
            os.makedirs(REPO_PATH + '/' + self.root_path)

        os.chdir(REPO_PATH + '/' + self.root_path)

        if username is None:
            ACCOUNT = config.get(self.url_type, 'account-1')
            PASSWORD = config.get(self.url_type, 'password-1')
            ret = os.system('git clone -b %s https://%s:%s@' % (self.branch, ACCOUNT, PASSWORD) +
                            self.url.replace('https://', '') + ' ' + self.repo_name)
        else:
            ret = os.system('git clone -b %s https://%s:%s@' % (self.branch, username, password) +
                            self.url.replace('https://', '') + ' ' + self.repo_name)

        if ret != 0:
            raise DownloadError('Opps, download failed! Please ensure the validation of the project.')

    def delete_repo(self):
        if self.is_repo_existed():
            os.chdir(REPO_PATH + '/' + self.url_type)
            os.system('rm -rf ' + self.repo_path_prefix)

    def delete_from_db(self):
        MysqlOperation.delete_from_mysql(
            tablename='repository',
            field = 'uuid',
            value = self.uuid
        )

    def insert_into_db(self):
        try:
            if self.is_in_db() is False:
                MysqlOperation.insert_into_mysql(
                    tablename='repository',
                    params={
                        'description': self.description,
                        'language': self.language,
                        'repository_id': self.repository_id,
                        'local_addr': self.rel_path,
                        'url': self.url,
                        'uuid': self.uuid,
                        'is_private': self.is_private
                    }
                )
                MysqlOperation.insert_into_mysql(
                    tablename='relation',
                    params={
                        'repository_id': self.repository_id,
                        'repository_uuid': self.uuid,
                        'branch': self.branch
                    }
                )
        except Exception as e:
            raise e

    def get_uuid(self):
        result = MysqlOperation.get_data_from_mysql(
            tablename='repository',
            params={'local_addr': self.rel_path},
            fields=['uuid']
        )
        if len(result) == 0:
            self.insert_into_db()   #本地有repo但数据库中不存在repo
        else:
            self.uuid = result[0][0]


def get_api_url(project_url, type):
    if type == 'gitlab':
        return 'https://gitlab.com/api/v4/projects/' + project_url[19:].replace('/', '%2F')
    elif type == 'github':
        return 'https://api.github.com/repos/' + project_url[19:]


def get_url_type(project_url):
    patterns = ('gitlab.com', 'github.com')
    for pattern in patterns:
        if pattern in project_url:
            return pattern[:-4]
    return None


def get_vcs_type(project_url):
    dic = {'github.com': 'git', 'gitlab.com':'git'}
    patterns = ('github.com', 'gitlab.com')
    for pattern in patterns:
        if pattern in project_url:
            return dic[pattern]


def get_project_info(url, url_type):
    flag = 0
    while True:
        try:
            if url_type is None:
                return None
            else:
                response = requests.get(get_api_url(url, url_type), timeout=15, headers=API_HEADER[url_type])
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
            if 'command' in json_data and json_data['command'] == 'stop-consumer' :
                consumer.close()
                break
            else:
                url = json_data['url']
                project_id = json_data['projectId']
                username = None
                password = None
                url_type = get_url_type(url)
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
                    project_info = None if url_type is None else get_project_info(url, url_type)

                if project_info is None:
                    send_failed_msg(project_id)
                else:
                    repository = Repository(project_info, url, url_type, json_data['private'], branch)
                    if not repository.is_repo_existed():
                        handler = RepositoryHandler(repository, username, password)
                        handler.start()

                    else: #密码是否正确
                        try:
                            repository.get_uuid()
                        except Exception as e:
                            log(e.__str__())
                            traceback.print_exc()
                            send_failed_msg(project_id)
                        else:
                            try:
                                download_message = {'repoId': repository.uuid, 'local_addr': repository.rel_path,
                                                    'max_index': 0, 'flag': 'first added and existed'}
                                send_msg(host=KAFKA_HOST, recv=KAFKA_TOPIC_3, msg=download_message)
                                repo_message = {
                                    'projectId': project_id,
                                    'language': repository.language,
                                    'VCS-Type': repository.vcs_type,
                                    'status': 'Downloaded',
                                    'description': repository.description,
                                    'repoId': repository.uuid
                                }
                                send_msg(host=KAFKA_HOST, recv=KAFKA_TOPIC_1, msg=repo_message)
                            except Exception as e:
                                log(e.__str__())
                                traceback.print_exc()