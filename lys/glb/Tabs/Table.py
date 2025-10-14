
from lys.widgets import TableModifyWidget, SidebarWidget
from lys.Qt import QtWidgets

class TableTab(SidebarWidget):
    """Widget to show table settings. Do not instanciate this class except in MainWindow."""

    def __init__(self):
        super().__init__("Table")
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
        self.show(True)

    def __closed(self):
        self._table = None
        self.__setWidget()
        self.show(False)

    def __setWidget(self, wid=None):
        if wid is None:
            wid = QtWidgets.QWidget()
        if self._widget is not None:
            self._layout.removeWidget(self._widget)
            self._widget.deleteLater()
        self._widget = wid
        self._layout.insertWidget(0, self._widget)
