#!/usr/bin/python3
#-*-coding:utf-8-*-

import os
import time
import threading

import utils
import worker

    
#isdigit()/isalpha()/isalnum()
while True:
    print('''
    ################################################################
    #### 请输入选项：                                           ####
    #### 1.查看当前的共享目录和同步目录（默认）                 ####
    #### 2.创建新的共享目录（输入目录后生成共享串）             ####
    #### 3.创建新的同步目录（需要提供：同步目录地址/共享串）    ####
    #### 4.删除单个或清空共享目录                               ####
    #### 5.删除单个或清空同步目录                               ####
    #### 0.退出程序                                             ####
    ################################################################''')
    choice = input("    请输入编号：")
    
    dws = worker.DataWorker('servers')
    dwc = worker.DataWorker('clients')
    if choice.isdigit() and int(choice) == 2:
        #输入目录地址，然后自动生成一个共享目录并打印一个UUID
        while True:
            path = input("作为服务端的共享目录地址[请输入绝对路径]：")
            try:
                sharekey = worker.makeserver(path)
            except IOError as e:
                print(e)
            except Exception as e:
                print(e)
            else:
                print("创建共享目录成功[共享串]：%s"%sharekey)
                break
            
    elif choice.isdigit() and int(choice) == 3:
        #输入目录地址，同时需要输入一个UUID，会自动同步远程目录
        while True:
            skey = input("同步的共享串[请输入32位的密串]：")
            path = input("作为客户端的同步目录地址[请输入绝对路径]：")
            if not skey or not path:
                break
            try:
                sharekey = worker.makeclient(skey, path)
            except IOError as e:
                print(e)
            except Exception as e:
                print(e)
            else:
                print("创建同步目录成功[路径]：%s"%sharekey)
                break
    elif choice.isdigit() and int(choice) == 4:
        #删除共享目录，删除一个或多个
        print('')
        serverlist = dws.load()
        if serverlist is not None and len(serverlist) > 0:
            utils.log("[中控台]本机作为服务端的共享目录：")
            count = 0
            for item in serverlist:
                count+=1
                print("{}.[{}] [{}]:{}".format(
                    count,
                    item['sharekey'],
                    time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item['addtime'])),
                    item['folder']))
        else:
            utils.log("[中控台]本机未设置共享目录")
            
        dval = input("删除的共享目录[请输入编号或共享串，输入ALL则清空]：")
        tmplist = serverlist[:]
        if dval.isdigit() and 0 < int(dval) <= len(tmplist):
            serverlist.pop(int(dval)-1)
            dws.dump(serverlist)
            print("删除成功：%s"%dval)
        elif dval.isalnum() and len(dval) == 32:
            count = 0
            for item in tmplist:
                if item.get('sharekey') == dval:
                    serverlist.pop(count)
                    count = -1
                    break
                count+=1
            if count == -1:
                dws.dump(serverlist)
                print("删除成功：%s"%dval)
            else:
                print("找不到记录：%s"%dval)
        elif dval == 'ALL':
            dws.dump([])
            print("删除清空%s条记录成功"%len(serverlist))
        else:
            print("输入格式错误：%s"%dval)

    elif choice.isdigit() and int(choice) == 5:
        #删除同步目录，删除一个或多个
        print('')
        clientlist = dwc.load()
        if clientlist is not None and len(clientlist) > 0:
            utils.log("[中控台]本机作为客户端的同步目录：")
            count = 0
            for item in clientlist:
                count+=1
                print("{}.[{}] [{}]:{}".format(
                    count,
                    item['sharekey'],
                    time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item['addtime'])),
                    item['folder']))
        else:
            utils.log("[中控台]本机未设置同步目录")
            
        dval = input("删除的同步目录[请输入编号或共享串，输入ALL则清空]：")
        tmplist = clientlist[:]
        if dval.isdigit() and 0 < int(dval) <= len(tmplist):
            clientlist.pop(int(dval)-1)
            dwc.dump(clientlist)
            print("删除成功：%s"%dval)
        elif dval.isalnum() and len(dval) == 32:
            count = 0
            for item in tmplist:
                if item.get('sharekey') == dval:
                    clientlist.pop(count)
                    count = -1
                    break
                count+=1
            if count == -1:
                dwc.dump(clientlist)
                utils.log("删除成功：%s"%dval)
            else:
                utils.log("找不到记录：%s"%dval)
        elif dval == 'ALL':
            dwc.dump([])
            utils.log("删除清空%s条记录成功"%len(clientlist))
        else:
            utils.log("输入格式错误：%s"%dval)
        
    elif choice.isdigit() and int(choice) == 0:
        #输入0表示退出程序
        exit(-1)
        
    else:
        #输入默认值回车，打印共享目录vs同步目录
        print('')
        print('')
        serverlist = dws.load()
        if serverlist is not None and len(serverlist) > 0:
            utils.log("[中控台]本机作为服务端的共享目录：")
            for item in serverlist:
                print("[{}] [{}]:{}".format(
                    item['sharekey'],
                    time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item['addtime'])),
                    item['folder']))
        else:
            utils.log("[中控台]本机未设置共享目录")

        clientlist = dwc.load()
        if clientlist is not None and len(clientlist) > 0:
            utils.log("[中控台]本机作为客户端的同步目录：")
            for item in clientlist:
                print("[{}] [{}]:{}".format(
                    item['sharekey'],
                    time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item['addtime'])),
                    item['folder']))
        else:
            utils.log("[中控台]本机未设置同步目录")
        #raise ValueError("SERVER or CLIENT")




if __name__ == '__main__':
    pass

