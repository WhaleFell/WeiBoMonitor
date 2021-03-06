'''
Author: whalefall
Date: 2021-02-27 13:59:09
LastEditTime: 2021-02-27 15:48:34
Description: 程序运行日志输出&记录(自己造轮子)
'''
from colorama import *  # 跨平台颜色输出

init(autoreset=True)  # 初始化,并且设置颜色设置自动恢复


'''
日志等级（level）	描述
DEBUG	最详细的日志信息，典型应用场景是 问题诊断
INFO	信息详细程度仅次于DEBUG，通常只记录关键节点信息，用于确认一切都是按照我们预期的那样进行工作
WARNING	当某些不期望的事情发生时记录的信息（如，磁盘可用空间较低），但是此时应用程序还是正常运行的
ERROR	由于一个更严重的问题导致某些功能不能正常运行时记录的信息
CRITICAL	当发生严重错误，导致应用程序不能继续运行时记录的信息
'''

class Logging(object):

    def __init__(self):
        pass

    def debug(self,msg):
        print(Fore.BLACK+Back.WHITE+"[DEBUG]"+msg)

    def info(self,msg):
        print(Fore.BLACK+Back.BLUE+"[INFO]"+msg)

    def warning(self,msg):
        print(Fore.YELLOW+Back.BLACK+"[WARNING]"+msg)

    def error(self,msg):
        print(Fore.RED+Back.BLACK+"[ERROR]"+msg)
    
    def critical(self,msg):
        print(Fore.BLACK+Back.RED+"[CRITICAL]"+msg)


