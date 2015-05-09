from tornado.ioloop import IOLoop
from multiprocessing.pool import ThreadPool

_workers = ThreadPool(20)


def run_background(func, callback=None, args=(), kwds={}):

    def _callback(result):
        IOLoop.instance().add_callback(lambda: callback(result))

    if callback is not None:
        _workers.apply_async(func, args, kwds, _callback)
    else:
        _workers.apply_async(func, args, kwds)
