# -- coding: utf-8 --
'''
Author: whalefall
Date: 2021-02-27 13:57:42
LastEditTime: 2021-05-31 16:04:28
Description: 微博简易监控程序
'''
import configparser
import datetime
import json
import os
import random
import re
import sqlite3
import sys
import time
from ast import literal_eval
from urllib.parse import urlencode
from urllib.request import urlretrieve

import requests
import urllib3
from fake_useragent import UserAgent
from lxml import etree

from function import log
from function import yiqin

urllib3.disable_warnings()

log = log.Logging()

# 获取脚本所在目录万能方法
path = os.path.split(os.path.realpath(__file__))[0]


def getConfig():
    config = configparser.ConfigParser()
    path_py = os.path.split(os.path.realpath(sys.argv[0]))[0]
    print("脚本目录:", path_py)
    path_config = os.path.join(path_py, "config.ini")

    if os.path.exists(path_config):
        config.read(path_config, encoding="utf-8")
        # 获取[OPQBot]配置
        weiboList = config.get("common", "weiboList")
        updateTime = config.get("common", "updateTime")
        CoolPushToken = config.get("common", "CoolPushToken")
        print('''
#################config.ini#####################
#     请核对配置信息!首次试用请修改config.ini
################################################
weiboList:%s
updateTime:%s
CoolPushToken:%s
################################################
        ''' % (weiboList, updateTime, CoolPushToken))
    else:
        config.add_section("common")
        config.set("common", "weiboList", "[6355968578,]")
        config.set("common", "updateTime", "60")
        config.set("common", "CoolPushToken", "")
        print("首次使用 请修改config.ini内容")
        config.write(open(path_config, "w"))

    return literal_eval(weiboList), int(updateTime), CoolPushToken

# 获取原始json数据


def getRawJson(uid):
    headers = {
        'authority': 'm.weibo.cn',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'accept': 'application/json, text/plain, */*',
        'mweibo-pwa': '1',
        'x-xsrf-token': 'fb7304',
        'x-requested-with': 'XMLHttpRequest',
        'sec-fetch-dest': 'empty',
        'user-agent': UserAgent().safari,
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'referer': r'https://m.weibo.cn/u/{}?uid={}&t=0&luicode=10000011&lfid=100103type%3D1%26q%3D%E5%85%89%E9%81%87'.format(uid, uid),
        'accept-language': 'zh-CN,zh;q=0.9',
    }

    params = {
        "page": "0",
        'uid': '%s' % uid,
        't': '0',
        'luicode': '10000011',
        'lfid': '100103',
        'type': '1',
        'type': 'uid',
        'value': '%s' % uid,
        # weibo用户标识符
        'containerid': '107603%s' % uid,
    }

    try:
        response = requests.get(
            'https://m.weibo.cn/api/container/getIndex', headers=headers, params=params, verify=False).json()
    except Exception as e:
        log.error("请求时出现错误(%s)60s后将重试" % e)
        time.sleep(60)
        getRawJson(uid)

    return response


# 处理json并生成结果集
def dispose(data):

    if data["ok"] != 1:
        log.error("数据不正常!60s后重试")
        time.sleep(60)
        dispose(getRawJson(uid))

    else:
        try:
            get_id = data["data"]["cards"][0]["mblog"]["user"]["id"]
            get_name = data["data"]["cards"][0]["mblog"]["user"]["screen_name"]
        except:
            log.error("用户信息获取失败!请检查UID")
        else:
            log.info("用户信息如下: UID:%s 名字:%s" % (get_id, get_name))

            # 获取微博
            blogs = data["data"]["cards"]

            blogsList = []
            for blog in blogs:
                html = blog["mblog"]["text"]
                blogId = blog["mblog"]["id"]
                created_at = blog["mblog"]["created_at"]
                created_at = datetime.datetime.strptime(
                    created_at, '%a %b %d %H:%M:%S +0800 %Y')
                timestamp = int(created_at.timestamp())
                created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
                # print(html)
                # 处理全文缺省内容
                if "全文" in str(html):
                    # https://m.weibo.cn/statuses/extend?id=4602297956709241
                    # print(blogId)
                    url = "https://m.weibo.cn/statuses/extend?id=%s" % blogId
                    headers = {
                        "Referer": "https://m.weibo.cn/status/%s" % blogId,
                        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Mobile Safari/537.36"
                    }
                    try:
                        resp = requests.get(
                            url, headers=headers, verify=False).json()
                        html = resp["data"]["longTextContent"]
                    except Exception as e:
                        log.error("获取全文失败!")

                htm = etree.HTML(html)

                # 敲黑板: string(.) 可以得到标签下的所有text()
                text = htm.xpath("string(.)").replace(
                    "\n", "").replace("\r", "")

                # print(created_at, text)
                # print("----------------------------------")

                content = {
                    "time": created_at,
                    "timestamp": timestamp,
                    "content": text,
                }
                blogsList.append(content)

            # print(blogsList)
            return get_name, blogsList


# sqlite3
def writeSQL(uid, timestamp, time, content):
    # newDir("sql")
    conn = sqlite3.connect(os.path.join(path, "weibo.db"))
    c = conn.cursor()

    # 新建UID表
    c.execute('''create table if not exists `{}` (
        `TimeStemp` int,
        `Time` varchar(225),
        `content` varchar(225),
        primary key(`TimeStemp`)
    )
    '''.format(uid))

    conn.commit()

    try:
        c.execute('''
        insert into `{}` (TimeStemp,Time,content) values (?,?,?)
        '''.format(uid), (timestamp, time, content))

        conn.commit()
    except sqlite3.IntegrityError:
        # log.info("UID:%s 未发现新数据" % (uid))
        return "0"
    except Exception as e:
        log.info("UID:%s 插入数据库出现未知错误! %s" % (uid, e))

        return "ERROR"
    else:
        # log.info("UID:%s 发现新数据 插入成功!%s" % (uid, time+" "+content))
        return "1"


# writeSQL(uid)

def update(uid, status="0"):
    # uid = "6355968578"
    name, result = dispose(getRawJson(uid))

    for blog in result:
        # print(blog)
        timestamp = blog.get("timestamp")
        times = blog.get("time")
        content = blog.get("content")
        res = writeSQL(uid, timestamp, times, content)

        # 数据初始化
        if status == "1":
            continue

        if res == "1":
            # 数据更新推送
            print("[NewWeiBo]%s发现新数据! UID:%s(%s) content:%s" %
                  (times, name, uid, content))
            return times, name, uid, content
        elif res == "0":
            continue
        else:
            log.error("出现错误!")
            return

    if status == "1":
        print("[Weibo]%s UID:%s 初始化完成!" %
              (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), uid))
    else:
        print("[Weibo]%s UID:%s(%s)无更新" %
              (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name, uid))

# CoolPush


class CoolPush():

    def __init__(self, token):
        self.token = token

        self.headers = {
            "User-Agent": "Mozilla/5.0 (WeiboMonitor; Win64; x64) Chrome/80.0.3987.163 Safari/537.36"
        }

    def pushSend(self, content):
        url = "https://push.xuthus.cc/send/%s" % (self.token)
        data = {
            "c": content,
        }
        try:
            resp = requests.get(url, headers=self.headers, params=data)

            if resp.json()["code"] != 200:
                log.error("[CoolPush]推送出现异常,响应:%s" % (resp.text))
            else:
                log.info("[CoolPush]推送成功")
        except:
            log.error("[CoolPush]推送失败!")

    def pushGoup(self, content):
        url = "https://push.xuthus.cc/group/%s" % (self.token)
        data = {
            "c": content,
        }
        try:
            resp = requests.get(url, headers=self.headers, params=data)

            if resp.json()["code"] != 200:
                log.error("[CoolPush]推送出现异常,响应:%s" % (resp.text))
            else:
                log.info("[CoolPush]推送成功")
        except:
            log.error("[CoolPush]推送失败!")


# cp = CoolPush("92f83d0596c7b553ea1df9f242e4fc46")
# cp.pushGoup("酷推测试")

# qq机器人
class OPQBot():
    def __init__(self, host, bot_qq):
        self.host = host
        self.bot_qq = int(bot_qq)
        self.api = "%s/v1/LuaApiCaller" % (host)

        self.params = {
            'qq': self.bot_qq,  # 机器人QQ号
            'funcname': "SendMsgV2",  # 调用方法类型
        }

        self.header = {
            "Accept": "application/json",
        }

    def postFun(self, data):

        try:
            resp = requests.post(self.api, params=self.params,
                                 data=json.dumps(data), headers=self.header)
            # print(resp)
            if resp.json()["Ret"] != 0:
                print("发送有异常 接口响应:{}".format(resp.text))
                return "101"
            else:
                print("发送成功~")
                return "200"
        except Exception as e:
            print("发送出现未知失败 错误:{}".format(e))
            return "0"

    def sendGoup(self, GoupID, ty, Content):
        if ty == "txt":
            data = {
                "ToUserUid": int(GoupID),
                "SendToType": 2,  # 1 为好友消息 2发送群消息  3发送私聊消息
                "SendMsgType": "TextMsg",
                "Content": Content
            }
        if ty == "pic":
            {
                "ToUserUid": 123456789,
                "SendToType": 2,
                "SendMsgType": "PicMsg",
                "PicUrl": "http://gchat.qpic.cn/gchatpic_new/304980169/636617867-2534335053-8E6B948D1E7A4F96DB5F9C4A6050FB02/0?vuin=123456789&term=255&pictype=0"
            }

        # 调用类的请求方法
        self.postFun(data)

    def sendFriendTxt(self, FriendID, Content):
        data = {
            "ToUserUid": int(FriendID),
            "SendToType": 1,  # 1 为好友消息 2发送群消息  3发送私聊消息
            "SendMsgType": "TextMsg",
            "Content": Content
        }

        # 调用类的请求方法
        self.postFun(data)

    # 发送群图片 Content为可选参数
    def sendGoupPic(self, GoupID, PicUrl, Content=""):
        data = {
            "ToUserUid": int(GoupID),
            "SendToType": 2,
            "SendMsgType": "PicMsg",
            "PicUrl": PicUrl,
            "Content": "[PICFLAG]"+Content
        }
        self.postFun(data)

    # 获取bot加入的群列表
    def getGroupList(self):
        param = {
            'qq': self.bot_qq,  # bot的QQ
            'funcname': 'GetGroupList'
        }
        datafrom = {
            "NextToken": ""
        }

        try:
            resp = requests.post(url=self.api, params=param,
                                 data=json.dumps(datafrom))
            TroopList = resp.json()["TroopList"]
            QQgroupList = []
            QQgroupList_all = []
            for QQgroup in TroopList:
                # print(QQgroup)
                groupID = QQgroup['GroupId']
                groupName = QQgroup['GroupName']
                group = {"groupID": groupID, "groupName": groupName}
                QQgroupList.append(groupID)
                QQgroupList_all.append(group)
            print("获取到的QQ群列表:", QQgroupList)
            print("详细信息:", QQgroupList_all)
            return QQgroupList
        except Exception as e:
            print("请求群列表出现未知失败 错误:{} 响应:{}".format(e, resp.status_code))
            return "0"

        '''       
        # 尝试通过旧版API 发送base64图片 (失败)
        # def sendGoupPic(self, groupID, base64):
        #     params = {
        #         'qq': self.bot_qq,  # bot的QQ
        #         'funcname': 'SendMsg'
        #     }
        #     data = {
        #         "toUser": groupID,  # 发到哪个QQ或者群号
        #         "sendToType": 2,  # 自己选择对应会话的数值
        #         "sendMsgType": "PicMsg",
        #         "content": "test",  # 文字消息
        #         "groupid": groupID,  # 群号
        #         "atUser": 0,
        #         "picUrl": "",  # 图片的url,iotqq会自动加Referer
        #         "picBase64Buf": base64,  # base64后的图片
        #         "fileMd5": "",  # 图片MD5,普通图片MD5貌似会过期,表情貌似不会
        #         "flashPic": "false"  # 闪照:仅群聊可用
        #     }

        #     resp = requests.post(self.api, params=params,
        #                          data=json.dumps(data), headers=self.header)

        #     print(resp.json())
        '''

# 推送部分


def push(content):
    # 实例化酷推
    cp = CoolPush(CoolPushToken)

    # opqbot
    bot = OPQBot("http://192.168.101.4:8888", 2593923636)
    try:
        cp.pushGoup("[%s]%s\n%s" % (name, times, content))
        cp.pushSend("[%s]%s\n%s" % (name, times, content))
        bot.sendGoup("1028871825", "txt",
                     "[%s]%s\n%s" % (name, times, content))
        bot.sendGoup("1077021541", "txt",
                     "[%s]%s\n%s" % (name, times, content))
    except:
        pass


if __name__ == "__main__":
    # uid = "6355968578"
    try:
        global CoolPushToken
        weiboList, updateTime, CoolPushToken = getConfig()
    except Exception as e:
        log.error("请检查配置文件config.ini")

    # bot.getGroupList()

    # 初始化
    for uid in weiboList:
        update(uid, "1")
        time.sleep(10)

    while True:
        for uid in weiboList:

            try:
                times, name, uid, content = update(uid)
                content_raw = "[%s]%s\n%s" % (name, times, content)
                # 推送部分
                print("PUSH %s,%s(%s),%s" % (times, name, uid, content))
                push(content_raw)

            except:

                pass

            time.sleep(updateTime)
