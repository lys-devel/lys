from ExtendAnalysis import plugin, load, display, append, edit, MultiCut
from LysQt.QtWidgets import QAction, QMenu

fileView = plugin.mainWindow().fileView


def _display():
    paths = fileView.selectedPaths()
    display(*[load(p) for p in paths])


def _multicut():
    paths = fileView.selectedPaths()
    for p in paths:
        w = load(p)
        MultiCut(w)


def _append():
    paths = fileView.selectedPaths()
    append(*[load(p) for p in paths])


def _edit():
    paths = fileView.selectedPaths()
    for p in paths:
        w = load(p)
        edit(w)


disp = QAction('Display', triggered=_display)
apnd = QAction('Append', triggered=_append)
mcut = QAction('MultiCut', triggered=_multicut)
edit = QAction('Edit', triggered=_edit)

menu = QMenu()
menu.addAction(disp)
menu.addAction(apnd)
menu.addAction(mcut)
menu.addAction(edit)

fileView.registerFileMenu(".npz", menu)
fileView.registerFileMenu(".png", menu)
fileView.registerFileMenu(".tif", menu)
fileView.registerFileMenu(".jpg", menu)
