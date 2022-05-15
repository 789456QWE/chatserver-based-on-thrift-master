import socket
import logging

# server

from thrift.server.TServer import TSimpleServer
from thrift.transport.TSocket import TServerSocket
from thrift.transport.TTransport import TBufferedTransportFactory
from thrift.protocol.TBinaryProtocol import TBinaryProtocolFactory, TProtocolFactory

# client
from thrift.transport.TSocket import TSocket
from thrift.transport.TTransport import TBufferedTransport
from thrift.protocol.TBinaryProtocol import TBinaryProtocol

# 这个就是Server中的service参数，根据的你的thrift服务的不同而变
# Service = importlib.import_module("gen-py.chatserver.ChatServer")


class Server:
    """
    封装的一个Server，为了使用更加的便捷方便
    """

    def __init__(self, addr, service, handler, server_cls=TSimpleServer, t_fact=TBufferedTransportFactory(),
                 p_fact: TProtocolFactory = TBinaryProtocolFactory(), transport_cls=TServerSocket):
        """
        参数有点多哈，不过不用怕，其实大部分都不用改，而且我也都上了缺省值
        :param addr: 监听在哪个地址和端口上，是一个二元组：(HOST, PORT)
        :param service: 你的thrift服务
        :param handler: 处理服务的handler，是一个handler实例
        :param server_cls: server的类型，我默认给你用的是TsimpleServer，用于测试，如果你真正上线的话，最好使用线程池的版本，我建议
        :param t_fact: TransportFactory，根据你的需求可以适当进行选择
        :param p_fact: ProtocolFactory，使用的协议，只要client跟server端匹配，符合你的需求就好
        :param transport_cls: 这东西基本不用变，详情查看官方文档
        """

        processor = service.Processor(handler)
        transport = transport_cls(*addr)
        self._addr = addr
        self.server = server_cls(processor, transport, t_fact, p_fact)

    def run_forever(self):
        """
        启动server，并监听在指定IP：PORT上
        :return:
        """

        print("Starting python server on {}:{}".format(*self._addr))
        try:
            self.server.serve()
        except BaseException as e:
            logging.error(e)
        finally:
            print("server has closed!")


class Client(TBufferedTransport):
    """
    封装的一个Client，为了使用更加的便捷方便
    """

    def __init__(self, raddr, service, protocol_cls=TBinaryProtocol, *args):
        """
        比server端的参数少多了，需要提供server的地址信息，以及哪个服务，协议就可以了
        :param raddr: server的地址信息，二元组：(HOST, PORT)
        :param service: 你的thrift服务
        :param protocol_cls: 通信时对数据的序列化的协议
        :param args: 其他
        """
        self.sock = TSocket(*raddr)
        super().__init__(self.sock, *args)

        self.protocol_cls = protocol_cls
        self.service = service
        self.addr = socket.gethostbyname(socket.gethostname())
        self.client = None

    def __enter__(self):
        """
        可以使用上下文管理器来管理资源，十分的人性！
        :return:
        """

        protocol = self.protocol_cls(self)
        self.client = self.service.Client(protocol)
        self.client.addr = self.addr
        self.open()

        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        同上
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """

        if exc_type:
            # TODO process exception
            pass
        self.close()
