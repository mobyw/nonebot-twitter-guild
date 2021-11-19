import sqlite3
from typing import List
from nonebot.log import logger


def Init():  # 初始化
    DB = sqlite3.connect('twitter.db')
    CUR = DB.cursor()
    CUR.execute('select count(*) from sqlite_master where type="table" and name = "user_list"')

    if CUR.fetchall()[0][0] == 0:
        CUR.execute('create table user_list (screen_name TEXT,name TEXT,id TEXT,tweet_id TEXT)')
        DB.commit()
        
    CUR.close()
    DB.close()


def AddNewUser(screen_name: str, name: str, id: str):  # 创建用户对应的表
    DB = sqlite3.connect('twitter.db')
    CUR = DB.cursor()
    table_name = '_' + screen_name
    CUR.execute('select count(*) from sqlite_master where type="table" and name = "{}"'.format(table_name))
    if CUR.fetchall()[0][0] == 0:
        CUR.execute("create table {} (id TEXT,cid TEXT,translate INTEGER)".format(table_name))
        CUR.execute('insert into user_list values("{}","{}","{}","")'.format(screen_name, name, id))
        DB.commit()
    else:
        logger.warning("用户记录已存在！")
    CUR.close()
    DB.close()


def AddCard(screen_name: str, ID: str, cid: int) -> int:  # 添加订阅信息 返回类型 记录是否已存在(int)1：存在
    DB = sqlite3.connect('twitter.db')
    CUR = DB.cursor()
    table_name = '_' + screen_name
    CUR.execute('select count(*) from {} where id="{}" and cid={}'.format(table_name, ID, cid))
    if CUR.fetchall()[0][0] != 0:
        logger.warning('当前频道记录已存在！')
        return 1
    CUR.execute('insert into {} values("{}",{},{})'.format(table_name, ID, str(cid), str(0)))
    DB.commit()
    CUR.close()
    DB.close()
    return 0


def DeleteCard(screen_name: str, ID: str, cid: int):  # 删除订阅信息 返回类型 删除是否成功(int)1:失败 ：成功
    DB = sqlite3.connect('twitter.db')
    CUR = DB.cursor()
    table_name = '_' + screen_name
    CUR.execute('select count(*) from {} where id="{}" and cid={}'.format(table_name, ID, cid))
    if CUR.fetchall()[0][0] == 0:
        logger.error('记录不存在！删除失败！')
        return 1
    CUR.execute('delete from {} where id="{}" and cid={}'.format(table_name, ID, cid))
    CUR.execute('select count(*) from {}'.format(table_name))
    if CUR.fetchall()[0][0] == 0:
        CUR.execute('drop table {}'.format(table_name))
        CUR.execute('delete from user_list where screen_name="{}"'.format(screen_name))
    DB.commit()
    CUR.close()
    DB.close()
    return 0


def DeleteGroupCard(ID: str):  # 删除群聊全部订阅列表
    users = GetUserList()
    for user in users:
        DeleteCard(user[0], ID, 1)


def GetCard(screen_name: str, ID: str, cid: int):  # 获取订阅信息
    res = []
    DB = sqlite3.connect('twitter.db')
    CUR = DB.cursor()
    table_name = '_' + screen_name
    CUR.execute('select * from {} where id="{}" and cid={}'.format(table_name, ID, cid))
    data = CUR.fetchall()
    if len(data) == 0:
        CUR.close()
        DB.close()
        return res
    else:
        res = data[0]
        CUR.close()
        DB.close()
        return res


def GetALLCard(screen_name: str):  # 获取全部订阅信息
    DB = sqlite3.connect('twitter.db')
    CUR = DB.cursor()
    table_name = '_' + screen_name
    CUR.execute('select * from {}'.format(table_name))
    data = CUR.fetchall()
    CUR.close()
    DB.close()
    return data


def TranslateON(screen_name: str, ID: str, cid: int):  # 开启推文翻译
    DB = sqlite3.connect('twitter.db')
    CUR = DB.cursor()
    table_name = '_' + screen_name
    CUR.execute('update {} set translate=1 where id="{}" and cid={}'.format(table_name, ID, cid))
    DB.commit()
    CUR.close()
    DB.close()


def TranslateOFF(screen_name: str, ID: str, cid: int):  # 关闭推文翻译
    DB = sqlite3.connect('twitter.db')
    CUR = DB.cursor()
    table_name = '_' + screen_name
    CUR.execute('update {} set translate=0 where id="{}" and cid={}'.format(table_name, ID, cid))
    DB.commit()
    CUR.close()
    DB.close()


def GetUserList() -> List:  # 获取用户列表
    res = []
    DB = sqlite3.connect('twitter.db')
    CUR = DB.cursor()
    CUR.execute('select * from user_list')
    data = CUR.fetchall()
    if len(data) == 0:
        CUR.close()
        DB.close()
        return res
    for index in data:
        res.append(index)
    CUR.close()
    DB.close()
    return res


def GetUserInfo(screen_name: str) -> List:  # 获取用户信息
    res = []
    DB = sqlite3.connect('twitter.db')
    CUR = DB.cursor()
    CUR.execute('select * from user_list where screen_name="{}"'.format(screen_name))
    data = CUR.fetchall()
    if len(data) != 0:
        res = data[0]
    CUR.close()
    DB.close()
    return res


def UpdateTweet(screen_name: str, tweet_id: str):  # 更新用户最新推文ID
    DB = sqlite3.connect('twitter.db')
    CUR = DB.cursor()
    CUR.execute('update user_list set tweet_id="{}" where screen_name="{}"'.format(tweet_id, screen_name))
    DB.commit()
    CUR.close()
    DB.close()


def Empty() -> bool:  # 全局用户列表为空
    DB = sqlite3.connect('twitter.db')
    CUR = DB.cursor()
    CUR.execute('select count(*) from user_list')
    if CUR.fetchall()[0][0] == 0:
        CUR.close()
        DB.close()
        return True
    else:
        CUR.close()
        DB.close()
        return False
