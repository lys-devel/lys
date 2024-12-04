import os
import numpy as np
from lys import glb
from lys.Qt import QtWidgets, QtGui

_fontPath = ".lys/settings/font.npy"


def _register():
    menu = glb.mainWindow().menuBar()
    font = menu.addMenu("Font")
    font.addAction("Set Font").triggered.connect(_setFont)
    default = font.addMenu("Default")
    default.addAction("Register as default").triggered.connect(_registerAsDefault)
    default.addAction("Set to default").triggered.connect(_setToDefault)
    default.addAction("Initialize").triggered.connect(_initializeFont)


def _setFont():
    (font, ok) = QtWidgets.QFontDialog.getFont(QtGui.QFont(glb.mainWindow().font()))
    if ok:
        glb.mainWindow().setFont(font)


def _registerAsDefault():
    os.makedirs(".lys/settings/", exist_ok=True)
    dic = {}
    font = glb.mainWindow().font()
    dic["font"] = font.toString()
    np.save(_fontPath, dic)


def _setToDefault():
    os.makedirs(".lys/settings/", exist_ok=True)
    if os.path.exists(".lys/settings/font.npy"):
        dic = np.load(_fontPath, allow_pickle=True).item()
        font = QtGui.QFont()
        font.fromString(dic['font'])
        glb.mainWindow().setFont(font)


def _initializeFont():
    glb.mainWindow().setFont(QtGui.QFont())


_register()
_setToDefault()
