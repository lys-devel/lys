"""
*glb* module gives global variables such as a instance of main window.

Functions used by general users are given in :mod:`.functions` module.

All global variables can NOT be directly imported from lys because these are used only by developers.

Developers should import lys.glb module to access global variables

Example:

    >>> from lys import glb
    >>> shell = glb.shell()
    >>> main = glb.mainWindow()

"""

from .shell import ExtendShell
from .MainWindow import MainWindow

_main = None


def mainWindow():
    """
    Return :class:`.MainWindow.MainWindow` object.

    *MainWindow* is used to realize new GUI functionalities in lys.
    See :class:`.MainWindow.MainWindow` for detailed description.

    """
    return _main


def shell():
    """
    Return :class:`.shell.ExtendShell` object.

    ExtendShell object is used to realize new functionalities in lys Python Interface.
    See :class:`.shell.ExtendShell` for detailed description.

    """
    return ExtendShell._instance


def createMainWindow(*args, **kwargs):
    """
    Create main window.

    This function is called by lys automatically, and thus users and developers need not to use this function.

    If you want to make custom launch script of lys, see :mod:`.__main__` module.
    """
    global _main
    _main = MainWindow(*args, **kwargs)


def restoreWorkspaces():
    """
    Restore workspaces.

    This function is called by lys automatically, and thus users and developers need not to use this function.

    If you want to make custom launch script of lys, see :mod:`.__main__` module.
    """
    global _main
    _main._restoreWorkspaces()
