
def db_connect(db_config):

    db_url = 'mysql+mysqlconnector://%s:%s@%s:%s/%s?charset=%s' % (
        db_config['user'],
        db_config['passwd'],
        db_config['host'],
        db_config['port'],
        db_config['db'],
        db_config['charset']
    )
    from sqlalchemy import create_engine

    engine = create_engine(db_url)

    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def log(string):
    import time
    t = time.strftime(r"%Y-%m-%d-%H:%M:%S", time.localtime())
    print("[%s]%s" % (t, string))

def from_path_get_branch(path, repo_name):
    import re
    branch_pattern = '/%s-([^/]{1,})_duplicate_fdse-[0-9]' % repo_name
    ret = re.findall(branch_pattern, path)
    if len(ret) == 0:
        raise Exception
    else:
        return ret[0]