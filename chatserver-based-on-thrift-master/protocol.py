import json


class Response:
    """
    用来得到一个响应信息，为了能用起来更加的方便
    """

    # TODOed 其实可以加上__slots__，能节约很多的内存，后续会实现
    __slots__ = ["status", "content"]

    def __init__(self, status: int = 200, content: str = "OK"):
        """
        相应的信息其实很少，只有状态码和响应的信息
        :param status:
        :param content:
        """

        self.status = status
        self.content = content

        # 用上__slots__就会简洁很多，现在很傻~
        # self._fields_name = "status", "content"
        # self._fields = self.status, self.content

    @classmethod
    def gen_response(cls, json_str):
        """
        还是有点用处的，将json转换成python的对象
        :param json_str:
        :return:
        """

        return cls(**json_str)

    def json(self):
        """
        便捷方法，将response实例序列化，得到json
        :return:
        """

        return json.dumps({key: getattr(self, key) for key in self.__slots__})


class Request:
    """
    与Response类似，不多介绍
    """

    __slots__ = ("uid", "token", "ip", "data")

    def __init__(self, uid: str = "",
                 # 该字段暂时未用到
                 token: str = "",
                 method: str = "",
                 data_type: str = "",

                 ip: str = "",
                 data: dict = None
                 ):
        self.uid = uid
        self.token = token
        self.ip = ip
        self.data = data if data else {}

        # self._fields_name = "uid", "ip", "data"
        # self._fields = self.uid, self.ip, self.data

    @classmethod
    def gen_request(cls, json_str):
        return cls(**json_str)

    def json(self):
        return json.dumps({key: getattr(self, key) for key in self.__slots__})
        # 遍历__slots__中的key，将其字典类型转化为json可接受的字符串类型
