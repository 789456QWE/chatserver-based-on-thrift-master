import importlib  # 在相对路径下进行引用
from queue import Queue

from thrift.server.TServer import TThreadPoolServer

from utils import json2req
from protocol import Response
from fast_server_client import Server

ChatServerService = importlib.import_module("gen_py.chatserver.ChatServer")


class ServerHandler:
    """
    server handler 用于处理用户的请求，其实就是RPC的函数，client只能提供的这些方法
    """

    # protocol of data

    def __init__(self):
        """
        好像也没啥，不过可以在此处实现对用户信息数据的初始化，如读取本地已存好的用户数据，不过此处未实现
        """

        self.global_group_dict = {}
        self.groups = {}
        self.users = {}

    def regist(self, request: str):
        """
        注册方法
        :param request: json字符串，很多都在client中有写，此处就不多说了
        :return:
        """

        request = json2req(request)  # 反序列化将json数据转化为字符串数据

        uid = request.uid
        password = request.data.get("password")

        # 用户不存在且用户ID，密码都给了，注意数据的互斥，应该加锁
        if uid and uid not in self.users and password:

            # 暂时先不加密
            self.users[uid] = password.strip()

            # 默认加入到全局群里
            self.global_group_dict[uid] = Queue()

            resp = Response(content="注册成功！").json()  # 将字典序列化成json字符串 返回response
            return resp

        return Response(status=400, content="注册失败！").json()

    def login(self, request: str):
        """
        登录方法
        :param request:
        :return:
        """

        request = json2req(request)
        uid = request.uid

        password = request.data.get("password")

        if self.users.get(uid) == password.strip():  # users{uid:password}
            return Response(content="登录成功！").json()

        return Response(status=400, content="登录失败！").json()

    def chat_default_group(self, request):
        """
        只要用户登录过，就可以在全局缺省的大群中聊天，当然我没做别的验证
        :param request: 请求
        :return:
        """

        # TODO 按理说，应该在server继续验证客户端的，但是目前先解决业务问题
        request = json2req(request)
        msg = request.data.get("msg")

        # 消息是客户端就做好了的
        # global_group_dict
        #  {
        #       "id" : {"消息1", "消息2", ...}
        #  }

        for queue in self.global_group_dict.values():  # 遍历所有用户的消息队列将缺省群众的消息给每个用户的消息队列中发送
            queue.put(msg) # 将客户端在缺省群中发送的所有消息压入每个用户的队列中

        return Response(content="消息发送成功").json()

    def show_default_group_mem(self, request):
        """
        调用此方法，其实不需要用户过多的数据，只要用户登录了就可以，所以为了统一，保留request
        :param request:
        :return:
        """

        return Response(content=str(self.global_group_dict.keys())).json()

    def create_group(self, request):
        """
        用户创建一个群聊，并将自己添加进去，具体细节请看README.md，下同
        :param request:
        :return:
        """

        request = json2req(request)
        group_name = request.data.get("group_name")
        uid = request.uid

        #groups：{
        #        group_name:uid;
        #}
        if group_name in self.groups:
            response = Response(status=400, content="该群已存在")
        else:
            self.groups[group_name] = {uid}
            response = Response(content="创建成功")

        return response.json()

    def show_groups(self, request):
        """
        与show_default_group_mem方法类似
        :param request:
        :return:
        """

        response = Response(content=str(self.groups))
        return response.json()

    def add_group(self, request):
        """
        添加群聊
        :param request:
        :return:
        """

        request = json2req(request)
        group_name = request.data.get("group_name")
        group = self._search_group(group_name)
        uid = request.uid

        if group and uid not in group:
            # 这肯定只有非False才会进来啊，pycharm犯傻了
            group.add(uid)
            return Response(content="添加成功").json()
        return Response(400, "添加失败").json()

    def _search_group(self, group_name: str):
        """
        搜索该群是否存在
        :param group_name: 要添加的群名称
        :return:
        """

        return self.groups.get(group_name)

    def search_group(self, request):
        """
        此方法是真正搜索group的api
        :param request:
        :return:
        """

        request = json2req(request)
        group_name = request.data.get("group_name")
        if group_name in self.groups:
            response = Response(content=group_name)
        else:
            response = Response(400, content="不存在这个群")
        return response.json()

    def chat_group(self, request):
        """
        在某个群中进行聊天
        :param request:
        :return:
        """

        request = json2req(request)
        data = request.data

        group_name = data.get("group_name")
        msg = data.get("msg")
        uid = request.uid

        if group_name in self.groups and uid in self.groups[group_name]:

            for user in self.groups[group_name]:
                self.global_group_dict[user].put(msg)

            return Response(status=200, content="消息发送成功").json()

        return Response(status=400, content="消息发送失败").json()

    def judge_user_in_group(self, uid: str, group_name: str):
        """
        工具方法，暂时就放这把，以后工具多了，在单独抽出个工具类或工具模块
        暂未实现
        :param uid: 被测试的用户ID
        :param group_name: 在哪个群中进行测试
        :return:
        """

        group = self._search_group(group_name)
        if group and uid in group:
            return group
        return ()

    def chat_with_single(self, request):
        """
        在指定的某个群中跟指定的某个人聊天
        :param request:
        :return:
        """

        request = json2req(request)
        data = request.data

        uid = request.uid
        group_name = data.get("group_name")
        ruid = data.get("ruid")
        msg = data.get("msg")

        group = self.judge_user_in_group(uid, group_name)
        if ruid in group:
            self.global_group_dict[ruid].put(msg)
            return Response(content="消息发送成功").json()

        return Response(status=400, content="联系不到他").json()

    def recv(self, request):
        """
        没用第三方queue，所以暂时就让client不断的请求这个接口把，要是用第三方queue
        就没这么多事了
        :param request:
        :return:
        """

        request = json2req(request)

        uid = request.uid
        queue = self.global_group_dict[uid]

        if not queue.empty():
            return queue.get()

        return ""


if __name__ == '__main__':
    server = Server(("127.0.0.1", 9999), ChatServerService, ServerHandler(), TThreadPoolServer)
    server.run_forever()
