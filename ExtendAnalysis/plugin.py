"""
*plugin* module gives tools for developers.

Functions used by general users are given in :mod:`.functions` module.

All plugin functions can NOT be directly imported from lys.

Developers should import plugin functions from lys.plugin module

Example:

    >>> from lys import plugin
    >>> plugin.registerFileLoader(".txt", function_to_load_txt)

"""

from .LoadFile import _addFileLoader
from .shell import ExtendShell
from .MainWindow import MainWindow

_main = None


def mainWindow():
    return _main


def shell():
    """
    Return :class:`.shell.ExtendShell` object.

    ExtendShell object is used to realize new functionalities in lys Python Interface.
    See :class:`.shell.ExtendShell` for detailed description.

    """
    return ExtendShell._instance


def _createMainWindow():
    global _main
    _main = MainWindow()


def registerFileLoader(type, func):
    """
    Register file loader.

    This function extend :func:`.function.load` function and enables lys to load various file types.

    Developers should implement file loader and register it by this function.

    Args:
        type (str): file extention, such as ".txt"
        func (function): function to load file.

    Example:
        Add file loader for .txt file using numpy.loadtxt.

        >>> import numpy as np
        >>> from lys import plugin
        >>> loader = lambda f: np.loadtxt(f)
        >>> plugin.registerFileLoader(".txt", loader)

        After executing above commands, :func:`.functions.load` function can load .txt files as numpy array.

        >>> from lys import load
        >>> arr = load("data.txt")
        >>> type(arr)
        numpy.ndarray
    """
    _addFileLoader(type, func)
