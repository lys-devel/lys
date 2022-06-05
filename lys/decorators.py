import functools
import warnings

from .errors import NotSupportedWarning


def avoidCircularReference(func, name="_avoidCircularFlg"):
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, name):
            setattr(self, name, False)
        if getattr(self, name) is True:
            return
        else:
            setattr(self, name, True)
            func(self, *args, **kwargs)
            setattr(self, name, False)
    return wrapper


def suppressLysWarnings(func):
    """
    Disable several lys warnings such as NotSupportedWarning. 
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", NotSupportedWarning)
            res = func(*args, **kwargs)
        return res
    return wrapper
