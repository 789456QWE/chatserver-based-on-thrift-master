def wrap1(*args):
    print(*args)

    def _ww(fn):
        def _wp():
            print("in wrap1")
            print(fn)
            res = fn()
            print("after wrap1")
            return res

        return _wp

    return _ww


def wrap2(*args):
    print(*args)

    def _ww(fn):
        def _wp():
            print("in wrap2")
            print(fn)
            res = fn()
            print("after wrap2")
            return res

        return _wp

    return _ww


@wrap1(1111111)
@wrap2(2222222)
def func():
    print("in func")


"""
1111111
2222222
in wrap1
<function wrap2.<locals>._ww.<locals>._wp at 0x7f3341cf01f0>
in wrap2
<function func at 0x7f3341cf00d0>
in func
after wrap2
after wrap1
"""
# func()

input()
print("ASDFADsgDsag")
input()
input()
