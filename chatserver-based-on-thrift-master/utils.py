import json
from functools import wraps

from hande import Handle
from protocol import Response, Request


def json2resp(json_str: str):
    """
    工具函数，将json数据转换成python对象，其实有点冗余，但是为了可读性，影响不大，下同
    :param json_str:
    :return:
    """

    data = json.loads(json_str)
    return Response.gen_response(data)


def json2req(json_str: str):
    """
    同上
    :param json_str:
    :return:
    """

    data = json.loads(json_str)
    return Request.gen_request(data)


def handle_response(handle_func=Handle.handle_default):
    """
    装饰器函数，用来给某一个请求方法注入一个处理相应的函数，注意，被注入的函数必须能处理两个参数
    分别为server的直接响应和client对象，该函数有无返回值目前来看影响不大
    :param handle_func: 处理响应的函数
    :return:
    """

    def _wrapper(fn):
        @wraps(fn)
        def _inner_wrapper(*args, **kwargs):
            res = fn(*args, **kwargs)

            if not res:
                return

            # 得到响应后在去处理响应
            res = handle_func(*res)
            return res

        return _inner_wrapper

    return _wrapper


def auth(need_login=True):
    """
    一个装饰器函数，用来修饰一个方法是否可以被当前的状态所访问
    如果当前处于登录的状态且need_login参数为True，则可以访问该API fn
    如果当前处于非登录状态且need_login参数为False，则可以访问该API fn
    其余所有情况不能访问该API fn
    :param need_login: 如果要被装饰的方法需要登录才能使用，则需要置为True，否则为False
    :return: 返回被包装的函数
    """

    def _auth(fn):
        @wraps(fn)
        def _wrapper(self):
            if not (self.status or need_login):
                # 没有登录才会进来
                return fn(self)

            if self.status and need_login:
                # 登录了才能进来
                return fn(self)
            if self.status:
                print("您已登录！")
            else:
                print("请先登录！")

            return ()

        return _wrapper

    return _auth
