#!/usr/bin/python3
#-*-coding:utf-8-*-

import os
import pickle
import time
import json,struct
import threading
import socket

import utils


'''记录共享目录并返回UUID'''
def makeserver(path):
    #目录必须存在
    if not os.path.exists(path):
        raise FileNotFoundError("路径[%s]不存在，请重新输入"%path)
    
    dws = DataWorker('servers')
    sharekey = utils.uniqid()
    result = dws.load()
    for res in result:
        while True:
            if res.get('sharekey') == sharekey:
                sharekey = utils.uniqid()
            else:
                break
        if res.get('folder') == path:
            raise UserWarning("共享目录正在使用中:%s"%res.get('folder'))
        
    item = {
        'sharekey':sharekey,
        'folder':path,
        'modtime':int(time.time()),
        'addtime':int(time.time())
        }
    dws.append(item)
    return sharekey
    

'''产生同步目录'''
def makeclient(sharekey, path):
    #目录必须存在且为空
    if not sharekey.isalnum or len(sharekey) != 32:
        raise UserWarning("共享串格式错误[要求32位长度]:%s"%sharekey)

    if not os.path.exists(path):
        raise FileNotFoundError("路径[%s]不存在，请重新输入"%path)
    
    dwc = DataWorker('clients')
    result = dwc.load()
    for res in result:
        if res.get('sharekey') == sharekey:
            raise UserWarning("共享串已设置同步目录:%s"%res.get('folder'))
        if res.get('folder') == path:
            raise UserWarning("同步目录正在使用中:%s"%res.get('folder'))
        
    item = {
        'sharekey':sharekey,
        'folder':path,
        'modtime':int(time.time()),
        'addtime':int(time.time())
        }
    dwc.append(item)
    return utils.uniqid()




class DataWorker():

    #需要加锁
    def __init__(self, kind):
        #kind:servers/clients
        assert kind in ['servers', 'clients', 'unworks']
        self.kind = kind
        self.lock = threading.Lock()

    '''读取pickle'''
    def load(self):
        self.lock.acquire()
        result = None
        path = 'config%s%s.pkl'%(os.sep, self.kind)
        if os.path.exists(path):
            with open(path, 'rb') as f:
                result = pickle.load(f)
        self.lock.release()
        return result

    '''覆盖存储pickle'''
    def dump(self, data):
        self.lock.acquire()
        path = 'config%s%s.pkl'%(os.sep, self.kind)
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        self.lock.release()
        return True

    '''列表操作：追加记录到指定文件'''
    def append(self, item, uniq=False):
        result = self.load()
        if uniq == True and item in result:
            return False
        result.append(item)
        self.dump(result)
        return result

    def sharekeys(self):
        sks = []
        result = self.load()
        for res in result:
            sks.append(res.get('sharekey'))
        return sks

    '''根据sharekey找到folder'''
    def folder(self, sharekey):
        data = self.load()
        for i in data:
            if i.get('sharekey') == sharekey:
                return i.get('folder')
        return None

    '''获取列表的全部指定字段'''
    def fields(self, field):
        fs = []
        result = self.load()
        for res in result:
            fs.append(res.get(field))
        return fs
    
    def get(self):
        pass
    
    def set(self):
        pass

    

class FileWorker():
    
    def __init__(self, sw, sharekey):
        self.rootpath = ''
        pass
    
    '''返回共享路径'''
    def basepath(self):
        return self.rootpath
    
    '''返回绝对路径'''
    def fullpath(self, filepath):
        return self.rootpath + filepath.replace('/', os.sep)

    '''返回相对路径(斜杠开头)'''
    def relapath(self, fullpath):
        return fullpath.replace(self.rootpath, '', 1).replace('\\', '/')



'''socket封装json消息包体'''
class SockWorker():

    def __init__(self, sk):
        self.sk = sk
        
    def send(self, info, encode='NONE'):
        #print(info)
        if encode == 'JSON':
            info = json.dumps(info)
        info = info.encode('utf-8')
        self.sk.send(struct.pack('i', len(info)))
        self.sk.send(info)
        return None
        
    def recv(self, decode='NONE'):
        size = self.sk.recv(4)
        if len(size)==0:
            return None
        size, = struct.unpack('i', size)
        info = self.sk.recv(size).decode('utf-8')
        #print(info)
        if decode == 'JSON':
            info = json.loads(info)
        return info


    '''发送文件流'''
    def sendfile(self, fullpath):
        with open(fullpath, 'rb') as f:
            for fl in f:
                self.sk.send(fl)
                
    '''存储文件流'''
    def recvfile(self, fullpath, filesize):
        recvsize = 0
        eachsize = 1024
        with open(fullpath, 'wb') as f:
            while not recvsize == filesize:
                if filesize - recvsize < eachsize:
                    eachsize = filesize - recvsize
                b = self.sk.recv(eachsize)
                f.write(b)
                recvsize+= len(b)
                

def testsocketserver(hostport):
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sk.bind(hostport)
    sk.listen(5)
    sk.setblocking(True)
    while True:
        conn,addr = sk.accept()
        print("%s:%d已连接"%addr)
        sw = SockWorker(conn)
        result = sw.recv()
        sw.send(result)
        conn.close()
        

if __name__ == '__main__':

    print("worker相关类库")

    print("----*----")

    fw = FileWorker(r'D:\python', None)
    print(fw.basepath())
    print(fw.fullpath('/abc'))
    print(fw.relapath(r'D:\python\test'))
    
    print("----*----")
    
    
    dws = DataWorker('servers')
    print(dws.load())
    dwc = DataWorker('clients')
    print(dwc.load())
    dwu = DataWorker('unworks')
    print(dwu.dump(['vff']))
    print(dwu.append('vff2'))
    print(dwu.load())

    print("----*----")
    
    try:
        print(makeserver(r'D:\shell\s3'))
    except UserWarning as reason:
        print(reason)
    
    try:
        print(makeclient('1a6a1f084c3f4e21bed7e3471f5a5eb6', r'D:\shell\c1'))
    except UserWarning as reason:
        print(reason)

    print("----*----")


    #socket
    hostport = ('127.0.0.1',10001)
    #服务端
    t = threading.Thread(target=testsocketserver, args=(hostport,))
    t.start()
    time.sleep(1)
    #客户端
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sk.connect(hostport)
    sw = SockWorker(sk)
    sw.send({"aaa":999}, encode='JSON')
    print(sw.recv(decode='JSON'))
    
    
    print("----*----")
