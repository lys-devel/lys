from lys import glb
from lys.Qt import QtWidgets


def _register():
    menu = glb.mainWindow().menuBar()
    font = menu.addMenu("Font")
    font.addAction("Set Font").triggered.connect(setFont)


def setFont():
    (font, ok) = QtWidgets.QFontDialog.getFont()
    if ok:
        glb.mainWindow().setFont(font)


_register()
