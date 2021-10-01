"""
*functions* module gives general functions for users and developers.

Functions related to global variables, such as main window, are given in :mod:`.glb` module.

Most of functions can be directly imported from lys Package:

>>> from lys import home
"""

import os
import sys


__home = os.getcwd()
"""home directory of lys"""
_dic = dict()
"""loader dictionary"""


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

    This function can be extended by :func:`registerFileLoader`

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
         :func:`registerFileLoader`, :func:`loadableFiles`
    """
    if os.path.isfile(file):
        _, ext = os.path.splitext(file)
        if ext in _dic:
            return _dic[ext](os.path.abspath(file), *args, **kwargs)
        else:
            print("Error on load because the loader for " + ext + " file is not registered.", file=sys.stderr)
            print("To load " + ext + " file, you should call registerFileLoader function.", file=sys.stderr)
            print("Type help(registerFileLoader) for detail.", file=sys.stderr)
            return None


def loadableFiles():
    """
    Returns list of extensions loadable by :func:`load`.

    Return:
        list of str: list of extensions

    Example:
        >>> from lys import loadableFiles
        >>> loadableFiles()
        [".npz", ".png", ".tif", "jpg", ".grf", ".dic"]
    """
    return _dic.keys()


def registerFileLoader(type, func):
    """
    Register file loader.

    This function extend :func:`load` function and enables lys to load various file types.

    Users should implement file loader and register it by this function.

    Args:
        type (str): file extention, such as ".txt"
        func (function): function to load file.

    Example:
        Add file loader for .txt file using numpy.loadtxt.

        >>> import numpy as np
        >>> from lys import registerFileLoader
        >>> registerFileLoader(".txt", np.loadtxt)

        After executing above commands, :func:`load` function can load .txt files as numpy array.

        >>> from lys import load
        >>> arr = load("data.txt")
        >>> type(arr)
        numpy.ndarray
    """
    _dic[type] = func


def edit(data):
    pass