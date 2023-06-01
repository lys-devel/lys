
from lys.widgets import TableModifyWidget
from lys.Qt import QtWidgets


class TableTab(QtWidgets.QWidget):
    """Widget to show table settings. Do not instanciate this class except in MainWindow."""

    def __init__(self):
        super().__init__()
        self._table = None
        self._widget = None
        self.__inilayout()
        self.__setWidget()

    def __inilayout(self):
        self._layout = QtWidgets.QVBoxLayout()
        self._layout.addStretch()
        self.setLayout(self._layout)

    def setTable(self, table):
        if self._table is not None:
            self._table.finalized.disconnect(self.__closed)
        self._table = table
        self._table.finalized.connect(self.__closed)
        self.__setWidget(TableModifyWidget(table))
        self.__setGlobalState(True)

    def __setGlobalState(self, b):
        from lys import glb
        tab = glb.mainWindow().tabWidget("right")
        list = [tab.tabText(i) for i in range(tab.count())]
        if "Table" in list:
            tab.setTabVisible(list.index("Table"), b)
            if b:
                tab.setCurrentIndex(list.index("Table"))
                glb.mainWindow()._side.setVisible(True)

    def __closed(self):
        self._table = None
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
