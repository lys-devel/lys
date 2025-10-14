
from lys.mcut import MultiCutWidget
from lys.Qt import QtWidgets
from lys.widgets import SidebarWidget

class MulticutTab(SidebarWidget):
    def __init__(self):
        super().__init__("MultiCut")
        self._objs = {}
        self._widget = None
        self.__inilayout()
        self.__setWidget()

    def __inilayout(self):
        self._layout = QtWidgets.QVBoxLayout()
        self.setLayout(self._layout)

    def setObject(self, obj):
        if obj not in self._objs:
            self._objs[obj] = MultiCutWidget(obj)
            self._layout.insertWidget(0, self._objs[obj])
            obj.closed.connect(self.__closed)
        elif self._widget == self._objs[obj]:
            return
        self.__setWidget(obj)
        self.show(True)

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
            self.show(False)
            self._widget = None
