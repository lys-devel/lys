from .FittingWindow import FittingWindow
from .Fitting import fit, sumFunction
from .Functions import _addFittingFunction


def addFittingFunction(func, name):
    """
    Add fitting function to the lys fitting module.

    Use :func:`lys.functions.registerFittingFunction` instead of this function.
    """
    return _addFittingFunction(func, name)
