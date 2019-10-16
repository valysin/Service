

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

REPO_TYPE = 'github'

LOCALHOST = '10.141.221.85'

REPO_PATH = '/home/fdse/user/issueTracker/repo'
LOCAL_ADDR_PREFIX = 'github'
REPO_ROOT_PATH_PATTERN = ''

GITHUB_TOKEN = '1b87888beee96384cd45087f26394e90abdda5f4'
GITLAB_TOKEN = ''
GIT_API_URL_PREFIX = 'https://api.github.com/repos/'
GIT_REMOTE_PREFIX = 'github.com/'
CLONE_PROTOCOL = 'https'

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