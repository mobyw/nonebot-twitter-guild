import os
import json

appid = ''
baidu_token = ''
token = ''
api_url = ''

# 配置文件目录 根据自己机器人结构修改
file = './data/twitter/config.json'

if os.path.exists(file):
    with open(file, 'r', encoding='utf-8')as fp:
        data = json.load(fp)
        if data.get('appid') != None:
            appid = data['appid']
        if data.get('baidu_token') != None:
            baidu_token = data['baidu_token']
        if data.get('api_url') != None:
            api_url = data['api_url']
else:
    data = {'appid': '', 'baidu_token': '', 'api_url': ''}
    os.makedirs(os.path.split(file)[0])
    with open(file, 'w', encoding='utf-8')as fp:
        json.dump(data, fp)
