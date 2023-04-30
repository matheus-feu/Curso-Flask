import time
from functools import wraps

from flask import make_response


def countTime(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        start = time.time()
        resp = function(*args, **kwargs)
        end = time.time()
        response = make_response(resp)
        response.headers['TimeCount'] = f"{end - start}s"
        kwargs["rsp"] = response

        return response

    return wrapper
