#-*- coding:utf-8 -*-

import threading
import queue
import time
import http.client
import urllib.request

lock = threading.Lock()
outFile = open('proxys.txt', 'w')
q=queue.Queue()

class CheckProxy(threading.Thread):
    def __init__(self,q):
        self.q=q
        threading.Thread.__init__(self)

    def run(self):
        while True:
            if self.q.qsize():
                proxy=q.get()
                headers = {
                    'User-Agent': 'curl/7.43.0',
                    'jmpews': 'proxy',
                    }
                try:
                    print(proxy)
                    conn = http.client.HTTPConnection(proxy, timeout=4.0)
                    conn.request(method='GET', url='http://proxy.jmpews.com:7777/echo', headers=headers )
                    resp = conn.getresponse()
                    rtxt=resp.read()
                    if rtxt.find(b'jmpews') > 0:
                        lock.acquire()
                        outFile.write(proxy+'\n')
                        lock.release()
                    else:
                        print('.')
                except Exception as e:
                    print(e)
                finally:
                    conn.close()
            else:
                break



# lock = threading.Lock()
def get_proxy_list():
    r=urllib.request.urlopen("http://xvre.daili666api.com/ip/?tid=556775634957175&num=20&delay=3&sortby=time&foreign=none")
    r=r.read().decode().split('\r\n')
    for p in r:
        q.put(p)
q.put('127.0.0.1:3128')
q.put('182.90.66.178:80')
get_proxy_list()
threads=[]
for i in range(5):
    threads.append(CheckProxy(q))

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

