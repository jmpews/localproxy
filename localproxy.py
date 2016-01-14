#-*- coding:utf-8 -*-

import tornado.web
import tornado.ioloop
import tornado.tcpserver
import tornado.tcpclient
import tornado.gen

class Connection(object):
    clients=set()
    proxys=set()
    def __init__(self,stream,address):
        Connection.clients.add(self)
        self._stream=stream
        self._proxystream=None
        self._address=address
        self.original_data=b''
        self.proxy_data=b''
        self.get_proxy()

    @tornado.gen.coroutine
    def get_proxy(self):
        while True:
            proxy_ip,proxy_port=Connection.proxys.pop()
            try:
                proxy_client=tornado.tcpclient.TCPClient()
                self._proxystream=yield proxy_client.connect(proxy_ip,proxy_port)
                print('Connected->'+proxy_ip+':'+str(proxy_port))
                self.read_original_request()
                Connection.proxys.add((proxy_ip,proxy_port))
                print('Reused->'+proxy_ip
                break
            except:
                print(proxy_ip+':'+str(proxy_port)+'failed and drop')



    def read_original_request(self):
        self._stream.read_until_close(streaming_callback=self.proxy_original_request)

    @tornado.gen.coroutine
    def proxy_original_request(self,data):
        self._proxystream.write(data,self.read_proxy_response)

    def read_proxy_response(self):
        self._proxystream.read_until_close(streaming_callback=self.send_proxy_response)
        # self._proxystream.read_until_close(streaming_callback=self.send_proxy_response)

    def send_proxy_response(self,data):
        self._stream.write(data)
        self._stream.close()
        self._proxystream.close()


# Connection.proxys.add(('127.0.0.1',3128))
import urllib.request
r=urllib.request.urlopen('http://xvre.daili666api.com/ip/?tid=556775634957175&num=5&foreign=none')
r=r.read().decode().split('\r\n')
for p in r:
    ip,port=p.split(':')
    Connection.proxys.add((ip,int(port)))
# import pdb;pdb.set_trace()
class ProxyTCP(tornado.tcpserver.TCPServer):
    def handle_stream(self, stream, address):
        Connection(stream,address)



server=ProxyTCP()
print('start proxy on 8888...')
server.listen(8888)
tornado.ioloop.IOLoop.current().start()

