from pathlib import Path
import webbrowser

import lys
from lys import glb
from lys.widgets import LysSubWindow


class manualView(LysSubWindow):

    def __init__(self, url):
        from lys.Qt import QtCore, QtWebEngineWidgets
        super().__init__()
        self.browser = QtWebEngineWidgets.QWebEngineView()
        self.browser.load(QtCore.QUrl.fromLocalFile(url))
        self.setWidget(self.browser)
        self.adjustSize()


def _register():
    menu = glb.mainWindow().menuBar()
    prog = menu.addMenu("Help")

    url = str(Path(lys.__file__).parent.parent) + "/docs/_build/html/index.html"
    menu1 = prog.addMenu("Open lys reference")
    proc = menu1.addAction("Internal browser")
    proc.triggered.connect(lambda: manualView(url))
    proc = menu1.addAction("External browser")
    proc.triggered.connect(lambda: webbrowser.open(url))

    proc = prog.addAction("Open dask status in browser")
    proc.triggered.connect(lambda: webbrowser.open(lys.core.DaskWave.client.dashboard_link))


_register()
