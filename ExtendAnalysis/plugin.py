"""
*plugin* module gives functions for developers.

Functions used by general users are given in :mod:`.functions` module.

All plugin functions can NOT be directly imported from lys.
Developers should import plugin functions from lys.plugin module

Example:

    >>> from lys import plugin
    >>> plugin.registerFileLoader(".txt", function_to_load_txt)

"""

from .LoadFile import _addFileLoader
from .MainWindow import _getMainMenu


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


def getMainMenu():
    """
    Return main menu of lys.

    This function is used to add new menu.

    Return:
        QMenuBar: menu bar of lys.

    Example:

        >>> from lys import plugin
        >>> act = plugins.getMainMenu.AddAction("Print")
        >>> act.triggered.connect(lambda: print("test"))
    """
    return _getMainMenu()
