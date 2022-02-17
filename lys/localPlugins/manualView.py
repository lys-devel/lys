from pathlib import Path

import lys
from lys import glb
from lys.widgets import LysSubWindow

from LysQt.QtCore import QUrl
from LysQt.QtWebEngineWidgets import QWebEngineView


class manualView(LysSubWindow):
    def __init__(self):
        super().__init__()
        url = str(Path(lys.__file__).parent.parent) + "/docs/_build/html/index.html"
        self.browser = QWebEngineView()
        self.browser.load(QUrl.fromLocalFile(url))
        self.setWidget(self.browser)
        self.adjustSize()


def _register():
    menu = glb.mainWindow().menuBar()
    prog = menu.addMenu("Help")

    proc = prog.addAction("Open lys reference")
    proc.triggered.connect(lambda: manualView())
    proc.setShortcut("Ctrl+M")


_register()
