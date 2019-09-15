from __future__ import (
    absolute_import,
    unicode_literals,
)

import functools


def decorated(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
