

ISSUE_TRACKER_MYSQL_DB = {
    'host':'10.131.252.160',
    'db':'issueTracker',
    'user':'root',
    'port':3306,
    'passwd':'root',
    'charset':'utf8mb4'
}

REDIS = {
    'host':'10.141.221.85',
    'password':'85redis',
    'db':5
}

LOCALHOST = '10.141.221.85'

REPO_PATH = '/home/fdse/user/issueTracker/repo'
LOCAL_ADDR_PREFIX = 'gitlab'
REPO_ROOT_PATH_PATTERN = ''

GITHUB_TOKEN = '1b87888beee96384cd45087f26394e90abdda5f4'
GITLAB_TOKEN = ''
GIT_API_URL = ''
GIT_REMOTE_PREFIX = ''

DOWNLOAD_ACCOUNT = {
    'user':'',
    'password':''
}
KAFKA_LOG_PATH = '/home/fdse/pythonApp/restfulAPI/log'

KAFKA_HOST = {
    'host-1':'10.141.221.85:9092'
}

KAFKA_GROUP_ID = 'test-consumer-group'

KAFKA_TOPIC = {
    'RepoManager':'RepoManager',
    'ProjectManager':'ProjectManager',
    'CompleteDownload':'CompleteDownload',
    'Scan':'Scan',
    'UpdateCommit':'UpdateCommit',
    'DuplicateRepo':'DuplicateRepo'
}

REPO_PATH_TYPE = {
    'git':'github'
}