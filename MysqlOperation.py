#coding:utf-8
import pymysql
import configparser
config = configparser.ConfigParser()
config.read('config.conf')

def insert_into_mysql(tablename, params={}, mode='single'):
    conn = pymysql.connect(
        host=config.get('IssueTrackerMysqlDB', 'host'),
        db=config.get('IssueTrackerMysqlDB', 'db'),
        user=config.get('IssueTrackerMysqlDB', 'user'),
        passwd=config.get('IssueTrackerMysqlDB', 'passwd'),
        charset=config.get('IssueTrackerMysqlDB', 'charset')
    )
    sql = "insert into %s " % tablename
    keys = params.keys()
    sql += "(`" + "`,`".join(keys) + "`)"               #字段组合
    values = list(params.values())                        #值组合，由元组转换为数组
    sql += " values (%s)" % ','.join(['%s']*len(values))  #配置相应的占位符
    cur = conn.cursor()
    if mode == 'single':
        cur.execute(sql, values)
        conn.commit()
        cur.close()
        conn.close()
    elif mode == 'multiple':
        insert_items = []
        flag = 0
        index = 0
        while True:
            temp = []
            for key in keys:
                if index == len(params[key]):
                    flag = 1
                    break
                temp.append(params[key][index])
            if flag == 1:
                break
            insert_items.append(temp)
            index += 1

        cnt = 0
        for item in insert_items:
            cur.execute(sql, item)
            cnt += 1
            if cnt % 30 == 0:
                conn.commit()
        conn.commit()
        cur.close()
        conn.close()
    else:
        raise Exception

def delete_from_mysql(tablename, field='uuid', value=''):
    conn = pymysql.connect(
        host=config.get('IssueTrackerMysqlDB', 'host'),
        db=config.get('IssueTrackerMysqlDB', 'db'),
        user=config.get('IssueTrackerMysqlDB', 'user'),
        passwd=config.get('IssueTrackerMysqlDB', 'passwd'),
        charset=config.get('IssueTrackerMysqlDB', 'charset')
    )
    sql = "delete from %s " % tablename
    sql += " where %s = '%s' " % (field, value)
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

def update_mysql(tablename, params={}, pk='uuid'):
    conn = pymysql.connect(
        host=config.get('IssueTrackerMysqlDB', 'host'),
        db=config.get('IssueTrackerMysqlDB', 'db'),
        user=config.get('IssueTrackerMysqlDB', 'user'),
        passwd=config.get('IssueTrackerMysqlDB', 'passwd'),
        charset=config.get('IssueTrackerMysqlDB', 'charset')
    )
    cur = conn.cursor()
    sql = "update %s set " % tablename
    keys = params.keys()
    for key in keys:                                  #字段与占位符拼接
        if key != pk:
            sql += "`" + key + "` = %(" + key + ")s,"
    sql = sql[:-1]                                   #去掉最后一个逗号
    # sql += " where uuid = %(uuid)s "                 #只支持按主键进行修改
    sql += " where %s = " % pk + "%" + "(%s)s" %pk
    cur.execute(sql, params)
    conn.commit()
    cur.close()
    conn.close()


def get_data_from_mysql(tablename=None, params={}, fields=[], order_field=None, order_by = 'desc', start=None, num=None, sql=None):
    order = ''
    limit = ''

    if order_field is not None:
        order = ' order by ' + order_field + ' ' + order_by

    if start is not None and num is not None:
        limit = ' limit ' + str(start) + ',' + str(num)

    conn = pymysql.connect(
        host=config.get('IssueTrackerMysqlDB', 'host'),
        db=config.get('IssueTrackerMysqlDB', 'db'),
        user=config.get('IssueTrackerMysqlDB', 'user'),
        passwd=config.get('IssueTrackerMysqlDB', 'passwd'),
        charset=config.get('IssueTrackerMysqlDB', 'charset')
    )
    if sql is not None:
        cur = conn.cursor()
        cur.execute(sql)
        ret = cur.fetchall()
        return ret
    else:
        sql = "select %s from %s " % ('*' if len(fields) == 0 else ','.join(fields), tablename)
        keys = params.keys()
        where = ""
        ps = []
        values = []
        if len(keys) > 0:  # 存在查询条件时，以与方式组合
            for key in keys:
                ps.append(key + " =%s ")
                values.append(params[key])
            where += ' where ' + ' and '.join(ps)
        cur = conn.cursor()
        cur.execute(sql + where + order + limit, values)
        ret = cur.fetchall()
        cur.close()
        conn.close()
        return ret
