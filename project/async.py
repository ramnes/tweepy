import functools

import gevent


def async(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        return gevent.get_hub().threadpool.apply(function, args, kwargs)
    return wrapper
