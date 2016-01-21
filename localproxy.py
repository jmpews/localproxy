#-*- coding:utf-8 -*-
import tornado.web
import tornado.ioloop
import tornado.tcpserver
import tornado.tcpclient
import tornado.gen
import datetime
proxys= open('proxys.txt', 'r')

from queue import Queue
class Connection(object):
    clients=set()
    proxys=Queue()
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
            proxy_ip,proxy_port=Connection.proxys.get()
            try:
                proxy_client=tornado.tcpclient.TCPClient()
                self._deadline = tornado.ioloop.IOLoop.current().time() + 3
                self._proxystream=yield tornado.gen.with_timeout(self._deadline,proxy_client.connect(proxy_ip,proxy_port))
                print('Connected->'+proxy_ip+':'+str(proxy_port))
                self._proxy=(proxy_ip,proxy_port)
                self.read_original_request()
                self.read_proxy_response()
                break
            except tornado.gen.TimeoutError:
                proxy_client.close()
                print(proxy_ip+':'+str(proxy_port)+'-timeout!')
            except ConnectionError:
                proxy_client.close()
                print(proxy_ip+':'+str(proxy_port)+'-connecterror!')
            except Exception:
                proxy_client.close()
                print(proxy_ip+':'+str(proxy_port)+'-error!')
                

    def onclose_original(self,data=None):
        print('close original')
        if data!=None and not self._stream.closed():
             print('cache data!!!!')
        if not self._proxystream.closed():
            self._proxystream.close()
        if not self._stream.closed():
            self._stream.close()

    def read_original_request(self):
        self._stream.read_until_close(callback=self.onclose_original,streaming_callback=self.proxy_original_request)

    def proxy_original_request(self,data):
        print(data)
        self._proxystream.write(data)

    @tornado.gen.coroutine
    def read_proxy_response(self):
        try:
            f= yield tornado.gen.with_timeout(datetime.timedelta(seconds=10),self._proxystream.read_until_close(streaming_callback=self.send_proxy_response))
            print('Reused->'+self._proxy[0]+':'+str(self._proxy[1]))
            Connection.proxys.put(self._proxy)
            if not self._proxystream.closed():
                self._proxystream.close()
            if not self._stream.closed():
                self._stream.close()
        except tornado.gen.TimeoutError:
            print('proxy_read_timeout')
            self._proxystream.close()
            self._stream.close()

    def send_proxy_response(self,data):
        print(data)
        self._stream.write(data)

print('获取到可用IP:')
for p in proxys:
    ip,port=p.strip().split(':')
    print(ip,port)
    Connection.proxys.put((ip,int(port)))
# import pdb;pdb.set_trace()
class ProxyTCP(tornado.tcpserver.TCPServer):
    def handle_stream(self, stream, address):
        Connection(stream,address)

server=ProxyTCP()
print('start proxy on 8888...')
server.listen(8888,'0.0.0.0')
tornado.ioloop.IOLoop.current().start()

