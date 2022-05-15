import time
import socket
import logging
import datetime
# import importlib
import threading
from threading import Thread

from hande import Handle
from protocol import Request
from fast_server_client import Client
from utils import json2resp, auth, handle_response

from gen_py.chatserver import ChatServer as ChatServerService

# ChatServerService = importlib.import_module("gen-py.chatserver.ChatServer")


class SimpleClient:
    """
    一个简单的前端的client实现，开发者可以基于thrift协议开发出其他版本的client，但是由于server端
    对发送的数据又进行了二次协议化，所以，client发送的消息(参数)必须严格要求，其实就是json，这样做的
    话，前后端处理也会更加方便，具体的json协议实现见README，相信你能看懂
    """

    # 这是发送的消息的一部分，主要为msg部分，这个可以改变，只要前后端相同即可
    msg_fmt = "{}:{} == {}  ->  {}"

    def __init__(self, uid=None, password=None, host="127.0.0.1", port=9999, delay=1.0):
        """
        如果是高级点的用户，我指的是能看懂py源码的，不是纯小白，那么可以直接在此处写好账号密码，就能直接
        登录，省事一点
        :param uid: 用户的唯一ID
        :param password: 用户的密码，注意，我在server端并没有做任何的加密处理
        :param host: 要连接的server的IP地址，一般情况下，这个东西是不会让用户修改的
        :param port: server的端口
        :param delay: 该参数是用户收消息的延迟，因为server的实现并未使用第三方的消息队列，只是用了一个threading.Queue
                      所以，迫不得已加了此参数，为的是让server可以服务更多的用户，否则server有一个线程就会被阻塞在此处
                      如果使用第三方的queue，那么就没有此类困扰了，因为用户就只有一个queue，会根据消息的格式来判断是什么
                      样的消息，这个以后还可以在实现协议，已解决具体的问题。
        """

        self.uid = uid
        self.password = password
        self.raddr = host, port
        self.ip = socket.gethostbyname(socket.gethostname())
        self.key = None
        self.client = None

        # 用来判断用户是否已经登录，目前server端没有做任何的有效性验证，简单实现下嘛
        self.status = None

        self.request = None

        # 用以实现recv方法何时可以真正的调用，只有登陆成功后才能知道从哪个queue中拿数据
        self.event = threading.Event()  # 通过threading.Event()可以创建一个事件管理标志，该标志（event）默认为False
        self._delay = delay

    def get_msg(self, msg):
        return self.msg_fmt.format(
            self.ip, self.uid, str(datetime.datetime.now())[:-4], msg)

    def run(self):
        """
        便捷方法，用来实现client的调度等，使用了一个封装过的Client，便于开发
        :return:
        """
        try:
            with Client(self.raddr, ChatServerService) as client:
                print("建立与服务器的连接")
                self.client = client

                # 内部开启了一个线程，等待信号满足，才能真正收消息
                self.recv()  #接受信息
                self.dispatcher()  # 判断用户想使用的功能
        except Exception as e:
            logging.error(e)

    def easy_act(self, act: dict, request_func):
        """
        跟easy_tran方法很像，不过主要是用来做一些动作的，如注册，登录，创建群，加群等等，其实前边的注册方法和登录方法也可以使用，
        而且会更加的方便，好吧，我前后代码不是很统一，我马上去改~~
        注意，此方法内部使用的是self.request，原因就是登录后，就可以复用那个请求中的状态信息，所以我又想到了一个问题，那么就是
        用户登录前没有那些状态信息，好吧，此方法也要修改，不过还好，不用改太多
        # TODOed 作为通用方法，修改一下，未登录时也能使用，而且看看能不能将此方法跟easy_tran方法进行合并，如果用起来不是很方便的话就算了
        # OK
        :param act: 要做哪些动作
        :param request_func: 请求方法
        :return: 返回响应
        """

        if not self.status:  # 判断是否登陆
            self.request = Request(**act)
        else:
            self.request.data.update(act) # 调用python内置函数进行数据更新

        js = self.request.json()  # 序列化数据，方便写入json
        resp = request_func(js) # 函数处理时使用json数据处理

        response = json2resp(resp)  # 函数的作用为将字符串转变成一个字典类对象，函数返回出来时需要用对象接受

        if self.status:
            for k in act.keys():
                self.request.data.pop(k)  # 如果用户以登录，将其字典数据（收到的消息）出栈，清空删除字典里的数据

        return response

    @handle_response()
    @auth(False)
    def regist(self):
        """
        注册账号的方法，以下所有的方法，都是粗略的实现，毕竟思路才是最重要的
        :return:
        """

        # 可以帮用户查询该ID是否存在，暂未实现
        self.uid = input("请输入你要注册的ID\n")
        self.password = input("请输入密码\n")

        print("ID为{}，密码为{}".format(self.uid, self.password))
        # 使用封装的一个Request类构造请求，使使用起来更加方便点
        register_data = {"ip": self.ip, "uid": self.uid, "data": {"password": self.password}}

        # 注意只能使用self.client跟server端进行通信，json2resp只是来将返回的json数据转成Response对象
        # 便于对数据的处理！！！
        response = self.easy_act(act=register_data, request_func=self.client.regist)

        return response, self

    @handle_response(Handle.handle_login)
    @auth(False)
    def login(self):
        """
        登录方法
        :return:
        """

        self.uid = input("请输入你的账号\n")
        self.password = input("请输入你的密码\n")
        print("ID为{}，密码为{}".format(self.uid, self.password))
        login_data = {"uid": self.uid, "ip": self.ip, "data": {"password": self.password}}

        response = self.easy_act(act=login_data, request_func=self.client.login)
        # request = Request(uid=self.uid, ip=self.ip, data={"password": self.password})
        # response = json2resp(self.client.login(request.json()))

        return response, self

    @handle_response()
    @auth(True)
    def chat_default_group(self):
        """
        在缺省的群中进行聊天，看此方法就是用了很多前边封装过的方法，是不是简洁多了，当然，处理相应的还没做
        等会就会更加的优雅了，而且会更加便于维护，我们不是简简单单的只是好看，便于使用和维护才是我的目的。
        :return:
        """
        try:
            msg = input("你想聊点啥？\n")
            print("你的消息为{}".format(msg))
            chat_data = {"msg": self.get_msg(msg)}
            response = self.easy_act(act=chat_data, request_func=self.client.chat_default_group)
            return response, self

        except Exception as e:
            print(e)

    @handle_response()
    @auth(True)
    def show_default_group_mem(self):
        """
        用来显示缺省群中都有哪些用户，下边的方法如果没什么特殊的东西，我就简写了奥
        :return:
        """

        response = self.easy_act({}, self.client.show_default_group_mem)

        return response, self

    @handle_response()
    @auth(True)
    def create_group(self):
        """
        创建群
        :return:
        """

        group_name = input("请输入你要创建的群名称\n")
        print("群名称为{}".format(group_name))
        response = self.easy_act({"group_name": group_name}, self.client.create_group)

        return response, self

    @handle_response()
    @auth(True)
    def show_groups(self):
        """
        显示当前共哪些群
        :return:
        """

        response = self.easy_act({}, self.client.show_groups)

        return response, self

    @handle_response()
    @auth(True)
    def add_group(self):
        """
        添加群
        :return:
        """

        group_name = input("请输入要添加的群名称\n")
        print("群名称为{}".format(group_name))
        response = self.easy_act({"group_name": group_name}, self.client.add_group)
        return response, self

    @handle_response()
    @auth(True)
    def search_group(self):
        """
        查询群
        :return:
        """

        group_name = input("请输入要查找的群名称\n")
        print("群名称为{}".format(group_name))
        response = self.easy_act({"group_name": group_name}, self.client.search_group)

        return response, self

    @handle_response()
    @auth(True)
    def chat_group(self):
        """
        在某个群中聊天
        :return:
        """

        group_name = input("你想在哪个群中聊天\n")
        msg = input("你想聊点啥\n")
        print("群名称为{}，聊天信息为{}".format(group_name, msg))

        chat_data = {
            "group_name": group_name,
            "msg": self.get_msg(msg)
        }

        response = self.easy_act(act=chat_data, request_func=self.client.chat_group)

        return response, self

    @handle_response()
    @auth(True)
    def chat_with_single(self):
        """
        在某个群中和某个人进行私聊
        :return:
        """

        group_name = input("在那个群里？\n")
        ruid = input("那个人的ID是多少?\n")
        msg = input("你想跟他聊点啥?\n")
        print("群名称为{}，ID为{}，信息为{}".format(group_name, ruid, msg))
        chat_data = {
            "group_name": group_name,
            "msg": self.get_msg(msg),
            "ruid": ruid
        }

        response = self.easy_act(act=chat_data, request_func=self.client.chat_with_single)

        return response, self

    def recv(self):
        """
        接收消息的方法，只有当用户登录后，才能真正开始工作，有点丑陋，~~
        如果是使用第三方队列的话，那么用户登陆成功后，将会返回用户在第三方
        队列的信息，然后直接请求第三方队列就好了，也就不用这么丑陋的代码了
        :return:
        """

        def _recv():
            if self.event.wait():  # 调用wait他会判断标志位是True还是False，是True继续执行，false则阻塞。event.set()使标志位变为True。
                while 1:
                    try:
                        msg = self.client.recv(self.request.json())
                        if msg:
                            print(msg)
                    except Exception as e:
                        print(e)
                        return
                    time.sleep(self._delay)

        # 成为daemon线程（守护线程）设置为True，所以用户只要退出后，默认该线程也会直接退出
        # start() 方法是启动一个子线程
        # run() 方法并不启动一个新线程，就是在主线程中调用了一个普通函数而已。

        Thread(target=_recv, daemon=True).start()


    def gen_func(self):
        """
        这个方法的代码丑是真的没有任何的办法的，毕竟怎么弄，都得有丑陋的地方，我就不追求别的了，毕竟我这个client
        只是简单的实现，主要是用于验证我的server没问题，思路，思路才是最重要的，但是也不能空耍嘴皮子~~~，下一个
        :return:
        """

        _func = {
            "1": self.regist,
            "2": self.login,
            "3": self.chat_default_group,
            "4": self.show_default_group_mem,
            "5": self.create_group,
            "6": self.show_groups,
            "7": self.add_group,
            "8": self.search_group,
            "9": self.chat_group,
            "10": self.chat_with_single,
            "11": self.exit
            # "7": self.show_group_mem,
        }
        return _func

    @classmethod
    def exit(cls):
        """
        退出方法，用户会失去所有的状态信息，不过他的身份信息还保存在server端，这点不用害怕，只不过你还等从新登录
        我其实可以写一个方法，保存用户的状态信息，让用户可以不用总是重新登录，这个其实很好写，但是算了把，没啥技术含量
        而且，我这个client也仅仅是用来玩，差不多就行了
        :return:
        """

        print("bye~")
        exit(0)

    def dispatcher(self):
        """
        真正的调度(分派，命令分发器)方法，用户可以键入命令，选择需要的功能，很简单不多说了就
        :return:
        """

        func = self.gen_func()

        try:
            while True:
                cmd = input("""
                1: 注册账号             2: 登录          3: 在缺省群中聊天
                4: 查看缺省群中有哪些人   5: 创建群聊       6: 显示已存在的群
                7: 添加入群             8: 查找群         9: 在群中聊天     
                10: 在群里跟别人私聊      11: 退出
                \n""")

                if not cmd:
                    continue
                func.get(cmd, lambda: None)() # 通过字典的kv值进行函数的调用

        except Exception as e:
            print(e, "~~~", "++")
            return


if __name__ == '__main__':
    host0 = "101.132.118.162"
    host1 = "127.0.0.1"
    cli = SimpleClient(host=host1, delay=0.5)
    cli.run()
