
from lys.widgets import ModifyWidget
from lys.Qt import QtWidgets


class GraphTab(QtWidgets.QWidget):
    """Widget to show graph settings. Do not instanciate this class except in MainWindow."""

    def __init__(self):
        super().__init__()
        self._canvas = None
        self._widget = None
        self.__inilayout()
        self.__setWidget()

    def __inilayout(self):
        self._layout = QtWidgets.QVBoxLayout()
        self._layout.addStretch()
        self.setLayout(self._layout)

    def setCanvas(self, canvas):
        if self._canvas is not None:
            self._canvas.finalized.disconnect(self.__closed)
        self._canvas = canvas
        self._canvas.finalized.connect(self.__closed)
        self.__setWidget(ModifyWidget(canvas))
        self.__setGlobalState(True)

    def __setGlobalState(self, b):
        from lys import glb
        tab = glb.mainWindow().tabWidget("right")
        list = [tab.tabText(i) for i in range(tab.count())]
        if "Graph" in list:
            tab.setTabVisible(list.index("Graph"), b)
            if b:
                tab.setCurrentIndex(list.index("Graph"))
                glb.mainWindow()._side.setVisible(True)

    def __closed(self):
        self._canvas = None
        self.__setWidget()
        self.__setGlobalState(False)

    def __setWidget(self, wid=None):
        if wid is None:
            wid = QtWidgets.QWidget()
        if self._widget is not None:
            self._layout.removeWidget(self._widget)
            self._widget.deleteLater()
        self._widget = wid
        self._layout.insertWidget(0, self._widget)