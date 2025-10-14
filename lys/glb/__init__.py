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
_side = []


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


def addSidebarWidget(widget):
    """
    Add sidebar widget in main window.

    Args:
        widget(lys.widgets.SidebarWidget): The sidebar widget
        title(string): The title of the tab.
    """
    _side.append(widget)
    if _main is not None:
        tab = mainWindow().tabWidget("right")
        tab.addTab(widget, widget.title)
        tab.setTabVisible(tab.count()-1, widget.visible)


def editCanvas(canvas):
    """
    Edit canvas by GUI.

    Args:
        canvas: The canvas to be edited.
    """
    tab = mainWindow().tabWidget("right")
    index = [tab.tabText(i) for i in range(tab.count())].index("Graph")
    tab.widget(index).setCanvas(canvas)


def editTable(table):
    """
    Edit table by GUI.

    Args:
        table: The table to be edited.
    """
    tab = mainWindow().tabWidget("right")
    index = [tab.tabText(i) for i in range(tab.count())].index("Table")
    tab.widget(index).setTable(table)


def editMulticut(mcut):
    """
    Open multicut by GUI.

    Args:
        mcut: The MuletiCut object.
    """
    tab = mainWindow().tabWidget("right")
    index = [tab.tabText(i) for i in range(tab.count())].index("MultiCut")
    tab.widget(index).setObject(mcut)


def startFitting(canvas):
    """
    Open fitting window.

    Args:
        canvas: The canvas to be fitted.
    """
    tab = mainWindow().tabWidget("right")
    index = [tab.tabText(i) for i in range(tab.count())].index("Fitting")
    tab.widget(index).setCanvas(canvas)


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
