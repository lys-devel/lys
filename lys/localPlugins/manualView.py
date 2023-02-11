from pathlib import Path
import webbrowser

import lys
from lys import glb
from lys.widgets import LysSubWindow


class manualView(LysSubWindow):

    def __init__(self):
        from lys.Qt import QtCore, QtWebEngineWidgets
        super().__init__()
        url = str(Path(lys.__file__).parent.parent) + "/docs/_build/html/index.html"
        self.browser = QtWebEngineWidgets.QWebEngineView()
        self.browser.load(QtCore.QUrl.fromLocalFile(url))
        self.setWidget(self.browser)
        self.adjustSize()


def _register():
    url = str(Path(lys.__file__).parent.parent) + "/docs/_build/html/index.html"
    menu = glb.mainWindow().menuBar()
    prog = menu.addMenu("Help")

    proc = prog.addAction("Open lys reference")
    proc.triggered.connect(lambda: webbrowser.open(url))
    proc.setShortcut("Ctrl+M")


_register()
