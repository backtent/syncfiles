#!/usr/bin/python3
#-*-coding:utf-8-*-

import threading
import socket
import socketserver

import utils
import scanlan
from worker import DataWorker
from worker import SockWorker


'''作为服务端监听局域网扫描并校验共享串'''
class AuthServer(socketserver.BaseRequestHandler):
    
    '''处理方法'''
    def handle(self):
        status, message = 200, "DEFAULT"
        try:
            #headrecv
            sw = SockWorker(self.request)
            sharekey = sw.recv()

            if sharekey is None:
                return None

            #校验共享串
            dws = DataWorker('servers')
            result = dws.load()
            for res in result:
                if res.get('sharekey') == sharekey:
                    #匹配到共享串
                    status, message = 200, "鉴权成功"
                    break
                else:
                    #未匹配到共享串
                    status, message = 404, "鉴权失败"

            utils.log("%s发起请求:[%d]%s"%(self.client_address, status, message))
            
            sw.send({'status':status, 'message':message}, encode='JSON')

        except ConnectionResetError:
            utils.log("[AuthServer]%s强迫关连接"%(self.client_address,))
        finally:
            pass


'''鉴权客户端'''
class AuthClient():

    def __init__(self, sharekeys):
        self.sharekeys = sharekeys
        self.alllist = []
        self.uselist = []
        self.dielist = []
        self.usedict = {}
        self.diedict = {}

    '''循环鉴权'''
    def handle(self):
        #返回开启了8820鉴权服务的主机列表
        self.scan(gate='192.168.1.0/24', port=[8820])
        
        #传入共享串去每个服务器鉴权
        for res in self.sharekeys:
            self.usedict[res] = []
            self.diedict[res] = []
            for al in self.alllist:
                self.check(al, res)

        #在线/离线
        return self.alllist, self.uselist, self.dielist, self.usedict, self.diedict

    '''返回指定网关的items列表'''
    def scan(self, gate=None, port=None, lan=True):
        #局域网
        sl = scanlan.Scanlan(gate, port)
        self.alllist = sl.scan().result()

        #城域网
        
        return None
    
        
    '''根据主机端口和共享串校验是否授权'''
    def check(self, hostport, sharekey):
        if len(sharekey) != 32:
            return False
        
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        try:
            #utils.log("[AuthClient]正在尝试连接AuthServer...")
            sk.connect(hostport)
        except ConnectionRefusedError:
            #utils.log("[AuthClient]AuthServer%s积极拒绝"%(hostport,))
            return False
        else:
            #utils.log("[AuthClient]成功连接AuthServer:%s"%(hostport,))
            pass

        #headsend
        sw = SockWorker(sk)
        sw.send(sharekey)
        info = sw.recv(decode='JSON')
        #print(info)
        if info.get('status') == 200:
            self.uselist.append(hostport[0])
            self.usedict[sharekey].append(hostport[0])
            #utils.log("%s:%d鉴权成功"%hostport)
            return True
        else:
            self.dielist.append(hostport[0])
            self.diedict[sharekey].append(hostport[0])
            #utils.log("%s:%d鉴权失败"%hostport)
            return False
            
        return None



    
'''后台跑本机的鉴权服务'''
def runserver(host=None, port=None):
    #监听本地的IP和端口元组,多线程socket连接
    if host is None:
        host = utils.getip()
    if port is None:
        port = 8820
        
    hostport = (host, port)
    utils.log("[控制台]鉴权服务正在监听%s:%d端口..."%hostport)
    #多线程socket连接
    auth = socketserver.ThreadingTCPServer(hostport, AuthServer)
    #保持服务监听线程持续
    auth.serve_forever()

    return None

    
if __name__ == '__main__':
    
    #返回成功SUCCESS或失败FAILED
    #'192.168.1.28', 8820

    #运行鉴权服务
    t = threading.Thread(target=runserver, args=())
    t.start()

    #从本地存储的client获取已配置的列表
    sharekeys = DataWorker('clients').sharekeys()
    #运行请求鉴权
    alllist, uselist, dielist, usedict, diedict = AuthClient(sharekeys).handle()
    utils.log("共享主机[%d]台，已授权[%d]台，未授权[%d]台"%(len(alllist),len(uselist),len(dielist)))
    print("局域网开放了8820端口的服务器:")
    print(alllist)
    print("已授权的共享主机：")
    print(uselist)
    print("未授权的共享主机：")
    print(dielist)
    print("鉴权细节：")
    print(usedict)
    print(diedict)

    t.join()
