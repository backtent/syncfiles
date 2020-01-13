#!/usr/bin/python3
#-*-coding:utf-8-*-

import time
import uuid
import socket
import telnetlib
import threading
import queue

from IPy import IP


class Scanlan():
    def __init__(self, ipgate, polist):
        self.ipgate = ipgate
        self.polist = polist
        
        self.ipfind = []
        self.ipiter = IP(ipgate)

        self.tlock = threading.Lock()

    def _scanip(self, ip, way, timeout=1):
        if way == 'socket':
            for pl in self.polist:
                sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sk.settimeout(timeout)
                try:
                    sk.connect((ip, pl))
                except Exception as e:
                    #self.tlock.acquire()
                    #print("%s:%d=%s"%(ip,pl,e))
                    #self.tlock.release()
                    pass
                else:
                    self.ipfind.append((ip, pl))
                finally:
                    sk.close()
                    
        else:
            tn = telnetlib.Telnet()
            for pl in self.polist:
                try:
                    tn.open(ip, pl, timeout=timeout)
                except Exception as e:
                    #self.tlock.acquire()
                    #print("%s:%d=%s"%(ip,pl,e))
                    #self.tlock.release()
                    pass
                else:
                    self.ipfind.append((ip, pl))
                finally:
                    tn.close()

    '''开始扫描端口'''
    def scaning(self, que=True, way='socket'):
        self.ipfind = []
        self.starttime = time.time()
        tl = []
        if que == True:
            q = queue.Queue()
            for ip in self.ipiter:
                q.put(str(ip))
            while not q.empty():
                t = threading.Thread(target=self._scanip, args=(q.get(), way))
                t.start()
                tl.append(t)
        else:
            for ip in self.ipiter:
                t = threading.Thread(target=self._scanip, args=(str(ip), way))
                t.start()
                tl.append(t)
            
        for i in tl:
            i.join()

        self.endtime = time.time()
        return self


        
    '''使用匿名函数高速扫描'''
    def scan(self, cls=True):
        #关于python线程扫描端口第一次丢包少了很多结果
        if cls == True:
            self.scan(False)# empty run once
        
        self.ipfind = []
        def scanfastput(q, il, pl):
            for i in il:
                for j in pl:
                    q.put((str(i), int(j)))
        
        def scanfastget(tn, v1, v2):
            try:
                tn.open(v1, v2, timeout=1)
            except Exception as e:
                #self.tlock.acquire()
                #print("%s:%d=%s"%(v1,v2,e))
                #self.tlock.release()
                pass
            else:
                self.ipfind.append((v1, v2))
            finally:
                tn.close()
                
        self.starttime = time.time()
        tl = []
        q = queue.Queue()
        n = telnetlib.Telnet()

        #生产者创建
        scanfastput(q, self.ipiter, self.polist)
        
        #消费者线程
        while not q.empty():
            kv = q.get()
            t = threading.Thread(target=scanfastget, args=(n, kv[0], kv[1]))
            t.start()
            tl.append(t)
            
        #全部线程阻塞
        for i in tl:
            i.join()
            
        self.endtime = time.time()
        return self
        

    def result(self):
        return self.ipfind

    def look(self, seeall=True):
        self.ipfind.sort()
        if seeall == True:
            for i in self.ipfind:
                print(i)

        print("LEN:%d,TIME:%s"%(len(self.ipfind), round(self.endtime-self.starttime,2)))
        return None

if __name__ == '__main__':

    sl = Scanlan('192.168.1.0/24', [21, 80, 3306, 8080, 8081])
    #sl = Scanlan('192.168.1.0/24', [80, 3306])
    sl.scan().look(True)
    #print(sl.scan().result())
    
    '''
    sp = Scanlan('192.168.1.0/24', [80])
    sp.scan(que=True, way='socket', evp=False)
    sp.look(False)
    
    sp = Scanlan('192.168.1.0/24', [21, 80, 3306, 8080, 8081])
    sp.scan(que=True, way='socket', evp=False)
    sp.look(False)
    
    sp = Scanlan('192.168.1.0/24', [21, 80, 3306, 8080, 8081])
    sp.scan(que=True, way='telnet', evp=False)
    sp.look(False)
    
    sp = Scanlan('192.168.1.0/24', [21, 80, 3306, 8080, 8081])
    sp.scan(que=False, way='socket', evp=False)
    sp.look(False)
    
    sp = Scanlan('192.168.1.0/24', [21, 80, 3306, 8080, 8081])
    sp.scan(que=False, way='telnet', evp=False)
    sp.look(False)
    '''
    
