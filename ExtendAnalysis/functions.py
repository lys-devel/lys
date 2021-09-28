"""
*functions* module gives general functions for users.

Functions related to making plugins are given in :mod:`.plugin` module.

Most of functions can be directly imported from lys:

>>> from lys import home
"""

import os
import sys

from .LoadFile import _load, _getExtentions

__home = os.getcwd()
sys.path.append(__home)


def home():
    """
    Return home directory of lys.

    All settings related to lys will be saved in .lys directory.

    Return:
        str: path to home directory
    """
    return __home


def load(file, *args, **kwargs):
    """
    Load various files.

    Loadable file extensions are given by :func:`loadableFiles`

    This function is extended by :func:`.plugin.registerFileLoader`

    Args:
        file (str): file path
        *args (any): positional arguments
        **kwargs (any): keyword arguments

    Return:
        Any: return value depends on file type

    Example:
        >>> from lys import load
        >>> w = load("wave.npz")
        >>> type(w)
        <lys.core.Wave>

    See also:
         :func:`.plugin.registerFileLoader`, :func:`loadableFiles`
    """
    return _load(file, *args, **kwargs)


def loadableFiles():
    """
    Returns list of extensions loadable by :func:`load`.

    Return:
        list of str: list of extensions

    Example:
        >>> from lys import loadableFiles
        >>> loadableFiles()
        [".npz", ".png", ".tif"]
    """
    return _getExtentions()


def edit(data):
    pass
