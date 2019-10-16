import os
import re

from redis import Redis
from config import config
from dao import RepositoryDao as Dao
from db.model import RepositoryModel
from libs.tool import log

REPO_PATH = config.REPO_PATH
REPO_ROOT_PATH_PATTERN = config.REPO_ROOT_PATH_PATTERN

KAFKA_HOST = config.KAFKA_HOST['host-1']
LOCALHOST = config.LOCALHOST
KAFKA_TOPIC_1 = config.KAFKA_TOPIC['RepoManager']
KAFKA_TOPIC_2 = config.KAFKA_TOPIC['ProjectManager']
KAFKA_TOPIC_3 = config.KAFKA_TOPIC['CompleteDownload']
KAFKA_TOPIC_6 = config.KAFKA_TOPIC['DuplicateRepo']

# KAFKA_GROUP_ID = config.get('KafkaGroup', 'id-1')

# MAX_POLL_RECORDS = int(config.get('Kafka', 'max_poll_records'))

GITHUB_TOKEN = config.GITHUB_TOKEN
GITLAB_TOKEN = config.GITLAB_TOKEN

API_HEADER = {
    'gitlab': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0',
               'Private-Token': GITLAB_TOKEN},
    'github': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0',
               'Authorization': 'token ' + GITHUB_TOKEN}
}

REDIS_HOST = config.REDIS['host']
REDIS_DB = config.REDIS['db']
REDIS_PASSWORD = config.REDIS['password']
GIT_REMOTE_PREFIX = config.GIT_REMOTE_PREFIX
CLONE_PROTOCOL = config.CLONE_PROTOCOL

class RepositoryService():

    def __init__(self, repository, username, password):
        self.username = username
        self.password = password
        self.repository = repository

    def get_parent_path(self):
        split = self.repository.local_addr.split('/')
        return '/'.join(split[:-1])

    def get_repo_name(self):
        split = self.repository.local_addr.split('/')
        return split[-1]

    def get_root_path(self):
        # local_addr: gitlab/a/b/c
        # return a/b/c
        split = self.repository.local_addr.split('/')
        return '/'.join(split[1:])

    def get_url_suffix(self):
        return re.findall(REPO_ROOT_PATH_PATTERN, self.repository.url)[0]

    def download(self, username=None, password=None):
        parent_path = self.get_parent_path()
        if not os.path.exists(REPO_PATH + '/' + parent_path):
            os.makedirs(REPO_PATH + '/' + parent_path)

        os.chdir(REPO_PATH + '/' + parent_path)

        branch = self.repository.branch
        dest = self.get_repo_name()
        git_remote = GIT_REMOTE_PREFIX + '/' + self.get_url_suffix()
        log('从%s开始clone...' % git_remote)
        if username is None:
            USERNAME = config.DOWNLOAD_ACCOUNT['user']
            PASSWORD = config.DOWNLOAD_ACCOUNT['password']
            src = '%s://%s:%s@%s' % (CLONE_PROTOCOL, USERNAME, PASSWORD, git_remote)
            # git clone -b <branch> <src> <dest>
            # git clone <protocol>://<username>:<password>@<remote>
            ret = os.system('git clone -b %s %s %s' % (branch, src, dest))
        else:
            src = '%s://%s:%s@%s' % (CLONE_PROTOCOL, username, password, git_remote)
            ret = os.system('git clone -b %s %s %s' % (branch, src, dest))

        return ret == 0

    def copy(self, username=None, password=None):

        r = Redis(host=REDIS_HOST, db=REDIS_DB, password=REDIS_PASSWORD)

        for i in range(3):
            os.chdir(REPO_PATH + '/' + self.get_parent_path())
            ret = os.system('cp -r %s %s' % (self.get_repo_name(), self.get_repo_name() + '_duplicate_fdse-' + str(i)))
            # 备份文件名：<repo_name>_duplicate_fdse-<index>  repo_name: <repo>-<branch>
            if ret != 0:
                raise Exception('生成副本失败！')
            else:
                r.lpush(self.repository.uuid, "%s-%s-%s" % (LOCALHOST, self.repository.branch, str(i)))
        # 发送给其他服务器 进行备份
        r.rpush(self.repository.uuid, 'none')

    def delete(self):
        repository_dao = Dao.RepositoryDao(self.repository)
        repository_dao.delete()

    def get_uuid_by_addr(self):
        repository_dao = Dao.RepositoryDao(self.repository)
        return repository_dao.get_uuid_by_local_addr()

    def is_existed(self):
        repository_dao = Dao.RepositoryDao(self.repository)
        return repository_dao.get_uuid_by_local_addr() != None

    def remove_repository(self):
        os.removedirs(REPO_PATH + '/' + self.repository.local_addr)

    def add_repository(self):
        download_state = self.download(self.username, self.password)
        if download_state is True:
            repository_dao = Dao.RepositoryDao(self.repository)
            repository_dao.insert()
        else:
            raise Exception('项目下载失败')