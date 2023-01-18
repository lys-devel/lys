import warnings
import functools


class NotImplementedWarning(Warning):
    pass


class NotSupportedWarning(Warning):
    pass


def suppressLysWarnings(func):
    """
    A decorator to disable several lys warnings such as NotSupportedWarning. 
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", NotSupportedWarning)
            res = func(*args, **kwargs)
        return res
    return wrapper


warnings.simplefilter("once", NotSupportedWarning)
