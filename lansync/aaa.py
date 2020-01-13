#!/usr/bin/python3
#-*-coding:utf-8-*-

import os
import time
import threading

import utils
import server
import client
import authority


utils.log("正在启动程序...")

#后台服务1：允许鉴权服务
#默认监控本机局域网IP的8820端口
auth = threading.Thread(target=authority.runserver, args=())

#后台服务2：监听本地的IP和端口元组
serv = threading.Thread(target=server.runserver, args=())

#后台服务3：允许客户端
clit = threading.Thread(target=client.runclient, args=())

#异步线程列表
auth.start()
serv.start()
clit.start()
tdlist = []
tdlist.append(auth)
tdlist.append(serv)
tdlist.append(clit)

time.sleep(1)

utils.log("[中控]线程后台执行中")
#print(s.getName())
#print(c.getName())
for td in tdlist:
    td.join()




if __name__ == '__main__':
    pass

