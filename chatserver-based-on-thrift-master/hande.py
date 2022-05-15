from status import Status


class Handle:

    # TODO 冗余代码，如下，可以根据状态码的不同，在分别加上不同的装饰器，已作出相应的处理方法，使更美观，更便于维护
    # TODO 如果有时间，我会做的，此处暂时略过，我在考虑，是使用装饰器好，还是直接使用函数，写一个处理响应的函数，毕竟
    # TODO 不是所有的处理响应的方法都相同，我先都试试，handle_func可能会用到 client instance 这个值。

    @staticmethod
    def handle_login(response, instance):
        # 好吧，写到这个方法的文档，我觉得实现一个处理响应的装饰器是很有必要的~~，马上就去干
        if response.status == Status.OK:
            instance.status = True
            instance.event.set()
        print(response.content)


    @staticmethod
    def handle_default(response, instance):
        print(response.content)