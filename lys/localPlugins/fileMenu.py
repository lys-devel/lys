from lys import glb, load, display, append, edit, MultiCut
from lys.Qt import QtWidgets

fileView = glb.mainWindow().fileView


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


disp = QtWidgets.QAction('Display', triggered=_display)
apnd = QtWidgets.QAction('Append', triggered=_append)
mcut = QtWidgets.QAction('MultiCut', triggered=_multicut)
edits = QtWidgets.QAction('Edit', triggered=_edit)

menu = QtWidgets.QMenu()
menu.addAction(disp)
menu.addAction(apnd)
menu.addAction(mcut)
menu.addAction(edits)

fileView.registerFileMenu(".npz", menu)
fileView.registerFileMenu(".png", menu)
fileView.registerFileMenu(".tif", menu)
fileView.registerFileMenu(".jpg", menu)
