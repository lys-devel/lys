
from lys.mcut import MultiCutWidget
from lys.Qt import QtWidgets


class MulticutTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self._objs = {}
        self._widget = None
        self.__inilayout()
        self.__setWidget()

    def __inilayout(self):
        self._layout = QtWidgets.QVBoxLayout()
        self._layout.addStretch()
        self.setLayout(self._layout)

    def setObject(self, obj):
        if obj not in self._objs:
            self._objs[obj] = MultiCutWidget(obj)
            self._layout.insertWidget(0, self._objs[obj])
            obj.closed.connect(self.__closed)
        elif self._widget == self._objs[obj]:
            return
        self.__setWidget(obj)
        self.__setGlobalState(True)

    def __setGlobalState(self, b):
        from lys import glb
        tab = glb.mainWindow().tabWidget("right")
        list = [tab.tabText(i) for i in range(tab.count())]
        if "MultiCut" in list:
            tab.setTabVisible(list.index("MultiCut"), b)
            if b:
                tab.setCurrentIndex(list.index("MultiCut"))
                glb.mainWindow()._side.setVisible(True)

    def __setWidget(self, obj=None):
        if self._widget is not None:
            self._widget.hide()
        if obj is not None:
            self._widget = self._objs[obj]
            self._widget.show()

    def __closed(self, obj):
        wid = self._objs[obj]
        del self._objs[obj]
        self._layout.removeWidget(wid)
        wid.deleteLater()
        if wid == self._widget:
            self.__setGlobalState(False)
            self._widget = None
