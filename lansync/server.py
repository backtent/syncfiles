#!/usr/bin/python3
#-*-coding:utf-8-*-
import os
import socketserver
import shutil

import utils
from worker import FileWorker
from worker import SockWorker
from worker import DataWorker


#server:监听端口，[接受]并[处理]目录和文件变动的操作请求

'''
使用socketserver基类
'''
class FileServer(socketserver.BaseRequestHandler):
    
    '''继承一次accept后的处理方法'''
    def handle(self):
        utils.log("[服务端]与客户端%s建立连接"%(self.client_address,))
        
        sw = SockWorker(self.request)
        sharekey = sw.recv()
        #print(sharekey)
        sfw = ServerFileWorker(sw, sharekey)
        #一次accept链接会话
        while True:
            sfw.doaction()
            '''try:
                sfw.doaction()
            except ConnectionResetError:
                utils.log("[控制台]客户主机%s强迫关闭了一个现有连接"%(self.client_address,))
                break
            except Exception as reason:
                utils.log("[控制台]handleException:%s"%reason)
                break
            finally:
                pass
            '''
        utils.log("[控制台]与客户端%s断开连接"%(self.client_address,))



'''
服务端文件作业sfw

传输文件[夹]
  |--创建文件[夹]
  |--
  
修改文件[夹]
移动文件[夹]
删除文件[夹]


常见HTTP错误代码大全：
600 成功
601 文件夹不存在
602 文件夹已存在
603 文件不存在
604 文件已存在但哈希不同
605 文件已存在且哈希相同
606 需要目录而路径非法
607 需要文件而路径非法
608 目标目录已存在
609 目标文件已存在
'''
class ServerFileWorker(FileWorker):
    
    def __init__(self, sw, sharekey):
        #是否使用哈希校验，为假则使用修改时间st_mtime校验self.usehash = False
        FileWorker.__init__(self, sw, sharekey)
        self.sw = sw
        self.sharekey = sharekey
        self.rootpath = DataWorker('servers').folder(sharekey)


    '''在操作之前先记录操作路径让本地监控忽略路径避免死循环'''
    def unwork(self, fullpath):
        dwu = DataWorker('unworks')
        info = dwu.load()
        if type(info) is list and fullpath not in info:
            info.append(fullpath)
        else:
            info = [fullpath,]
        dwu.dump(info)
        #utils.log('infos=%s'%info)
        return None

    '''根据来源判断客户端想我干啥'''
    def doaction(self):
        #接收握手信息1-
        hi = self.sw.recv(decode='JSON')
        if hi == None or hi.get('action') is None:
            raise Exception("客户端的来源请求recv为空")

        if self.rootpath == None:
            raise Exception("服务端配置sharekey失效")

        if hi.get('action') == 'unwork':
            return None

        #记录本地监控路径的变动到unworks的sharekey字典
        self.unwork(self.fullpath(hi['srcpath']))

        if hi.get('action') == 'createdir':
            self._createdir(hi['srcpath'])
            
        elif hi.get('action') == 'createfile':
            self._createfile(hi['srcpath'], hi['srcsize'], hi['srchash'])
            
        elif hi.get('action') == 'movedir':
            self._movedir(hi['srcpath'], hi['destpath'])
            
        elif hi.get('action') == 'movefile':
            self._movefile(hi['srcpath'], hi['destpath'])
            
        elif hi.get('action') == 'deletepath':
            self._deletepath(hi['srcpath'])
            
        elif hi.get('action') == 'deletedir':
            pass#self._deletedir(hi['srcpath'])
            
        elif hi.get('action') == 'deletefile':
            pass#self._deletefile(hi['srcpath'])
        else:
            pass
        
        return None

    

    '''创建目录createdir'''
    def _createdir(self, srcpath):
        status, message = (600, "MESSAGE-createdir")
        fullpath = self.fullpath(srcpath)
        if os.path.exists(fullpath):
            status = 602
        else:
            status = 601
            utils.log("[服务端]正在创建目录%s"%srcpath)
            os.mkdir(fullpath)
            
        #发送握手信息2-
        self.sw.send({'status':status, 'message':message}, encode='JSON')


    '''创建文件createfile'''
    def _createfile(self, srcpath, srcsize, srchash):
        status, message = (600, "MESSAGE-createfile")
        fullpath = self.fullpath(srcpath)

        #若文件存在且哈希值相同则不传输
        if os.path.exists(fullpath):
            if utils.filehash(fullpath) == srchash :
                utils.log("[服务端]文件哈希值一致:%s"%(srcpath))
                status, message = (605, "文件存在,哈希一致")
            else:
                status, message = (604, "文件存在,哈希不一致")
        else:
            status, message = (603, "服务端无该文件")

        #发送握手信息2-
        self.sw.send({'status':status, 'message':message}, encode='JSON')

        if status == 603 or status == 604:
            seesize = utils.getsize(srcsize)
            utils.log("[服务端]正在传输文件：[%s]%s"%(seesize, srcpath))
            self.sw.recvfile(fullpath, srcsize)
            utils.log("[服务端]文件传输完成：[%s]%s"%(seesize, srcpath))
        
        #conn.sendall(b'SUCCESS')
        return True

    
    '''移动目录movedir'''
    def _movedir(self, srcpath, destpath):
        status, message = (600, "MESSAGE-movedir")
        d1 = self.fullpath(srcpath)
        d2 = self.fullpath(destpath)
            
        if not os.path.exists(d1):
            status, message = (601, "源目录不存在")
        elif not os.path.isdir(d1):
            status, message = (606, "需要移动目录而路径非法:"+srcpath)
        elif os.path.exists(d2) and os.path.isdir(d2):
            status, message = (608, "目标目录存在")
        else:
            shutil.move(d1, d2)
            status, message = (600, "移动成功:%s=>%s"%(srcpath, destpath))
        
        #发送握手信息2-
        self.sw.send({'status':status, 'message':message}, encode='JSON')
        return True

    
    '''移动文件movefile'''
    def _movefile(self, srcpath, destpath):
        status, message = (600, "MESSAGE-movefile")
        f1 = self.fullpath(srcpath)
        f2 = self.fullpath(destpath)
        if not os.path.exists(f1):
            status, message = (601, "源文件不存在")
        elif not os.path.isfile(f1):
            status, message = (607, "需要移动文件而路径非法:"+srcpath)
        elif os.path.exists(f2) and os.path.isfile(f2):
            status, message = (609, "目标文件存在")
        else:
            shutil.move(f1, f2)
            status, message = (600, "移动成功:%s=>%s"%(srcpath, destpath))
        
        #发送握手信息2-
        self.sw.send({'status':status, 'message':message}, encode='JSON')
        return True

    def _deletepath(self, srcpath):
        #客户端删除目录或文件无法判断是目录亦或文件而服务端可以
        fullpath = self.fullpath(srcpath)
        if os.path.isdir(fullpath):
            return self._deletedir(srcpath)
        else:
            return self._deletefile(srcpath)
    
    '''删除目录deletedir'''
    def _deletedir(self, srcpath):
        status, message = (600, "MESSAGE-deletedir")
        fullpath = self.fullpath(srcpath)
        if not os.path.exists(fullpath):
            status, message = (601, "源目录不存在")
        elif not os.path.isdir(fullpath):
            status, message = (606, "需要删除目录而路径非法:"+srcpath)
        else:
            shutil.rmtree(fullpath)
            status, message = (600, "删除成功:%s"%(srcpath,))
        
        #发送握手信息2-
        self.sw.send({'status':status, 'message':message}, encode='JSON')
        return True

    '''删除文件deletefile'''
    def _deletefile(self, srcpath):
        status, message = (600, "MESSAGE-deletefile")
        fullpath = self.fullpath(srcpath)
        if not os.path.exists(fullpath):
            status, message = (601, "源文件不存在")
        elif not os.path.isfile(fullpath):
            status, message = (607, "需要删除文件而路径非法:"+srcpath)
        else:
            os.remove(fullpath)
            status, message = (600, "删除成功:%s"%(srcpath,))
        
        #发送握手信息2-
        self.sw.send({'status':status, 'message':message}, encode='JSON')
        return True




'''服务端运行入口函数'''
def runserver(hostport=None):
    if hostport is None:
        hostport = (utils.getip(), 8821)
        
    utils.log("[服务端]正在监听%s:%d端口..."%hostport)

    #多线程socket连接
    serv = socketserver.ThreadingTCPServer(hostport, FileServer)
    #保持服务监听线程持续
    serv.serve_forever()

    

if __name__ == '__main__':

    #监听本地的IP和端口元组
    runserver()
    
