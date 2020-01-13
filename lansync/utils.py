#!/usr/bin/python3
#-*-coding:utf-8-*-

__all__ = ['log', 'filehash', 'filetime', 'pathmake']

import os
import time
import socket
import hashlib
import threading
import uuid

'''日志内容统一输出'''
tlock = threading.Lock()
def log(txt):
    tlock.acquire()
    print("" + time.strftime('%Y-%m-%d %H:%M:%S') + " " + format(txt))
    tlock.release()

'''文件的哈希值sha1计算'''
def filehash(fp):
    if not os.path.isfile(fp):
        return ''
    
    while True:
        try:
            f = open(fp, 'rb')
        except PermissionError:
            time.sleep(1)
            continue
        else:
            break
        
    hh = hashlib.sha1()
    while True:
        b = f.read(8096)
        if not b:
            break
        hh.update(b)
    f.close()
    return hh.hexdigest()


'''判断文件是否完整'''
'''
def fileover(fp):
    #若文件大小正在变动则延迟一下PermissionError
    s1, s2 = 0, 1
    while s1 != s2:
        print(s1)
        s1 = os.stat(fp).st_size
        time.sleep(1)
        s2 = os.stat(fp).st_size
    return s1
fileover(r'D:\shell\test\Y470Y470PY570_WIN7x64.exe')
'''
        
'''无异常递归移动文件或文件夹'''
'''def surechange(path):
    pass'''

'''无异常递归删除文件或文件夹'''
'''def suredelete(path):
    pass'''

'''无异常递归创建文件夹'''
'''def surecreate(path, fp=None):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass
    return True'''

'''
获取可视化文件尺寸
B/KB/MB/GB/TP/PB/EB/ZB/YB/BB
'''
def getsize(byte, assoc=False):
    assert byte >=0
    size, unit = (0, 'B')
    if byte < 1024:
        size, unit = (byte, 'B')
    elif byte/1024 < 1024 :
        size, unit = (byte/1024, 'KB')
    elif byte/1048576 < 1024 :
        size, unit = (byte/1024/1024, 'MB')
    elif byte/1073741824 <= 1024 :
        size, unit = (byte/1024/1024/1024, 'GB')
    elif byte / 1099511627776 <= 1024 :
       size, unit = (byte/1024/1024/1024/1024, 'TB')
    else:
        size, unit = (byte/1125899906842624, 'PB')

    if assoc == True:
        return (size, unit)

    return '%.2f %s'%(size, unit)


def getname():
    return socket.getfqdn(socket.gethostname())

def getip(ifname='lo', ipv6=False):
    #环回地址：局域网IP
    return socket.gethostbyname(socket.getfqdn(socket.gethostname()))
    
    #主机地址：城域网IP
    '''import fcntl, struct
    skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inet = fcntl.ioctl(skt.fileno(), 0x8915, struct.pack('256s',ifname[:15]))
    return socket.inet_ntoa(inet[20:24])'''

def getmac(sep='-'):
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return sep.join([mac[e:e+2] for e in range(0,11,2)]).upper()


'''根据主机ID和序列号产生当前机器的唯一标识符'''
def computer():
    return str(uuid.uuid1())

'''产生随机UUID'''
def uniqid():
    return str(uuid.uuid4().hex)

    
if __name__ == '__main__':
    log("RUN:")
    log(filehash('utils.py'))


    #surechange(r'D:\shell\test\dd')
    #suredelete(r'D:\shell\test\dd')
    #surecreate(r'D:\shell\test\dd')

    print(getsize(1024))
    print(getsize(1048576))
    print(getsize(1073741824))
    print(getsize(1099511627776))


    print(getname())
    print(getip())
    print(getmac())

    print(computer())
    print(uniqid())

