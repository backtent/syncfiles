#!/usr/bin/python3
#-*-coding:utf-8-*-
import os
import socket
import time
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import utils
from worker import FileWorker
from worker import SockWorker
from worker import DataWorker
from authority import AuthClient


#client:本地目录和文件[监听]变动，[发送]给远程服务器


'''
文件系统监听
监控到文件变动就将变动分发到指定的服务端
'''
class FileMonitor(FileSystemEventHandler):
    '''
    event.is_directory
    event.src_path[dest_path]
    event.event_type
    event.key
    '''
    def __init__(self, sharekey, hostlist):
        FileSystemEventHandler.__init__(self)
        self.cfws = []
        for ip in hostlist:
            hostport = (ip, 8821)
            #与服务端保持长连接
            sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            try:
                utils.log("[客户端]正在尝试连接服务端...")
                sk.connect(hostport)
            except ConnectionRefusedError:
                utils.log("[客户端]目标计算机%s积极拒绝"%(hostport,))
                continue
            else:
                utils.log("[客户端]成功连接服务端:%s"%(hostport,))
            sw = SockWorker(sk)
            sw.send(sharekey)
            cfw = ClientFileWorker(sw, sharekey)
            #将目录的传输任务追加到文件服务，选中目录后循环发送到各个主机
            self.cfws.append(cfw)
            
        utils.log("[客户端]成功连接服务设备数:%d"%(len(self.cfws),))
            

        
    def on_any_event(self, e): 
        utils.log("========FileMonitor Syncing for a file========")
        if False:
            print(e, e.key)
            print("src_path:"+e.src_path)
            print("is_directory:"+format(e.is_directory))

        
    def on_created(self, e):
        
        for cfw in self.cfws:
            if cfw.unwork(e.src_path):
                break
            if e.is_directory:
                utils.log("[监控器]创建目录：%s"%(e.src_path))
                cfw.createdir(cfw.relapath(e.src_path))
            else:
                utils.log("[监控器]创建文件：%s"%(e.src_path))
                cfw.createfile(cfw.relapath(e.src_path))

    def on_moved(self, e):
        for cfw in self.cfws:
            if cfw.unwork(e.src_path):
                break
            if e.is_directory:
                utils.log("[监控器]移动目录：%s => %s"%(e.src_path, e.dest_path))
                cfw.movedir(cfw.relapath(e.src_path), cfw.relapath(e.dest_path))
            else:
                utils.log("[监控器]移动文件：%s => %s"%(e.src_path, e.dest_path))
                cfw.movefile(cfw.relapath(e.src_path), cfw.relapath(e.dest_path))


    def on_modified(self, e):
        for cfw in self.cfws:
            if cfw.unwork(e.src_path):
                break
            if e.is_directory:
                utils.log("[监控器]修改目录：%s"%e.src_path)
            else:
                utils.log("[监控器]修改文件：%s"%e.src_path)
                cfw.createfile(cfw.relapath(e.src_path))

    def on_deleted(self, e):
        for cfw in self.cfws:
            if cfw.unwork(e.src_path):
                break
            if True:
                utils.log("[监控器]删除路径：%s"%e.src_path)
                #删除目录或文件比较特殊，路径已经消失无法判断是目录亦或文件
                cfw.deletepath(cfw.relapath(e.src_path))





#需要传输的绝对路径:
#源文件1大小：563 KB (577,410 字节)
#源文件2大小：615 KB (630,016 字节)
#源文件3大小：259 KB (265,807 字节)
#源文件4大小：891 KB (913,246 字节)
#源文件5大小：285 KB (292,258 字节)
#xszr09.mkv 源文件 402 MB (421,832,408 字节)
#                  402 MB (421,832,408 字节)
#filelist = [r'zz1.txt', r'sondir/zz2.txt', r'me.jpg', r'tts.exe', r'tts.7z']

'''
客户端文件作业cfw
'''
class ClientFileWorker(FileWorker):
    def __init__(self, sw, sharekey):
        super().__init__(sw, sharekey)
        self.sw = sw
        self.sharekey = sharekey
        self.rootpath = DataWorker('clients').folder(sharekey)


    '''检查相对路径是否不需要处理'''
    def unwork(self, fullpath):
        dwu = DataWorker('unworks')
        info = dwu.load()
        #utils.log('infoc=%s'%info)
        if info is None or type(info) != list:
            #utils.log('action-unwork'+self.sharekey)
            return False
        if fullpath in info:
            dwu.dump(info.remove(fullpath))
            self.sw.send({'action':'unwork'}, encode='JSON')
            return True
        return False
    

    '''创建目录createdir'''
    def createdir(self, srcpath):
        fullpath = self.fullpath(srcpath)
        if not os.path.exists(fullpath):
            utils.log("[客户端]目录%s不存在"%fullpath)
            return False
        
        info = {'action':'createdir', 'srcpath':srcpath}
        #发送握手信息1-
        self.sw.send(info, encode='JSON')
        
        utils.log("[客户端]正在处理文件夹：%s"%srcpath)
            
        #接收握手信息2-
        info = self.sw.recv(decode='JSON')
        utils.log("[客户端]服务端响应:[%d]%s"%(info['status'],info['message'],))
        return None


    '''创建文件createfile'''
    def createfile(self, srcpath):
        fullpath = self.fullpath(srcpath)
        if not os.path.exists(fullpath):
            utils.log("文件%s不存在"%fullpath)
            return False
        
        info = {
            'action':'createfile',
            'srcpath':srcpath,
            'srcsize':os.stat(fullpath).st_size,
            'srchash':utils.filehash(fullpath)
            }
        
        #发送握手信息1-
        self.sw.send(info, encode='JSON')
        #utils.log("[客户端]正在处理文件：%s"%srcpath)
            
        #接收握手信息2-
        info = self.sw.recv(decode='JSON')
        utils.log("[客户端]服务端响应:[%d]%s"%(info['status'],info['message'],))

        if info['status'] == 605:
            utils.log("[客户端]跳过文件传输：%s"%srcpath)
        elif info['status'] in [603, 604]:
            utils.log("[客户端]正在传输文件：%s"%srcpath)
            self.sw.sendfile(fullpath)
            utils.log("[客户端]文件传输完成：%s"%srcpath)
        return None

    
    '''移动目录movedir'''
    def movedir(self, srcpath, destpath):
        info = {'action':'movedir', 'srcpath':srcpath, 'destpath':destpath}
        #发送握手信息1-
        self.sw.send(info, encode='JSON')
        #接收握手信息2-
        info = self.sw.recv(decode='JSON')
        utils.log("[客户端]服务端响应:[%d]%s"%(info['status'],info['message'],))
        return None
    
    '''移动文件movefile'''
    def movefile(self, srcpath, destpath):
        info = {'action':'movefile', 'srcpath':srcpath, 'destpath':destpath}
        #发送握手信息1-
        self.sw.send(info, encode='JSON')
        #接收握手信息2-
        info = self.sw.recv(decode='JSON')
        utils.log("[客户端]服务端响应:[%d]%s"%(info['status'],info['message'],))
        return None

    '''删除目录或文件'''
    def deletepath(self, srcpath):
        #删除目录或文件比较特殊，路径已经消失无法判断是目录亦或文件
        info = {'action':'deletepath', 'srcpath':srcpath}
        #发送握手信息1-
        self.sw.send(info, encode='JSON')
        #接收握手信息2-
        info = self.sw.recv(decode='JSON')
        utils.log("[客户端]服务端响应:[%d]%s"%(info['status'],info['message'],))
        return None
        
    
    '''删除目录deletedir'''
    """
    def deletedir(self, srcpath):
        info = {'action':'deletedir', 'srcpath':srcpath}
        #发送握手信息1-
        self.sw.send(info, encode='JSON')
        #接收握手信息2-
        info = self.sw.recv(decode='JSON')
        utils.log("[客户端]服务端响应:[%d]%s"%(info['status'],info['message'],))
        return None
    """
    
    '''删除文件deletefile'''
    """
    def deletefile(self, srcpath):
        info = {'action':'deletefile', 'srcpath':srcpath}
        #发送握手信息1-
        self.sw.send(info, encode='JSON')
        #接收握手信息2-
        info = self.sw.recv(decode='JSON')
        utils.log("[客户端]服务端响应:[%d]%s"%(info['status'],info['message'],))
        return None
    """

    '''一次完整传输'''
    def tranall(self):
        #遍历一次basepath的目录和文件并传输
        for top,dirs,files in os.walk(self.basepath()):
            for i in dirs:
                print("========")
                filepath = os.path.join(top, i)
                self.createdir(self.relapath(filepath))
            for j in files:
                print("========")
                filepath = os.path.join(top, j)
                self.createfile(self.relapath(filepath))
    
    def __del__(self):
        self.sk.close()
        utils.log("[客户端]全部处理完成，连接关闭")



'''执行一个监控客户端'''
def oneclient(sharekey, hostlist):
    basepath = DataWorker('clients').folder(sharekey)
    if os.path.exists(basepath):
        utils.log("[客户端]正在监控目录：%s"%basepath)
    else:
        utils.log("[客户端]{%s}对应的监控目录不存在：%s"%(sharekey,basepath))
        return None
    
    obs = Observer()
    fm = FileMonitor(sharekey, hostlist)
    #保持文件变动线程持续
    obs.schedule(fm, basepath, recursive=True)
    obs.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        obs.stop()
    obs.join()

    return None



'''客户端运行入口函数'''
def runclient():

    #运行请求鉴权
    sharekeys = DataWorker('clients').sharekeys()
    alllist, uselist, dielist, usedict, diedict = AuthClient(sharekeys).handle()
    utils.log("[客户端]共享主机[%d]台，已授权[%d]台，未授权[%d]台"%(len(alllist),len(uselist),len(dielist),))
    if len(uselist) == 0:
        utils.log("已授权主机为空，客户端尚未运行")
        return None
    
    #clients = DataWorker('clients').load()
    

    tlist = []
    for useitem in usedict.items():
        clit = threading.Thread(target=oneclient, args=(useitem))
        clit.start()
        tlist.append(clit)
        
    for tl in tlist:
        tl.join()
        
    return None

if __name__ == '__main__':
    
    
    #basepath = r'D:\shell\client'#本地的同步目录
    #hostport = ('127.0.0.1', 8821)#发送的远程IP和端口元组
    #tlist = runclient(basepath, hostport)
    print("正在运行runclient()...")
    runclient()
    
    
    
    #cfw.movedir('/h', '/i2')
    #cfw.movedir('/tts.7z', '/tts2.7z')
    #cfw.deletedir('/ff')
    #cfw.deletefile('/ff/dd.jpg')
    
    
    


