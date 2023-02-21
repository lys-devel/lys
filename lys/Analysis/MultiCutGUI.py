
from lys.Qt import QtWidgets, QtCore
from lys.widgets import LysSubWindow

from .MultiCut import MultiCutCUI
from .MultiCutGUIs import CutTab, AnimationTab, PrefilterTab, ExportDataTab


class _MultipleGrid(LysSubWindow):
    def __init__(self):
        super().__init__()
        self.__initlayout()
        self.resize(400, 400)

    def __initlayout(self):
        self.layout = QtWidgets.QGridLayout()
        w = QtWidgets.QWidget()
        w.setLayout(self.layout)
        self.setWidget(w)

    def Append(self, widget, x, y, w, h):
        for i in range(x, x + w):
            for j in range(y, y + h):
                wid = self.itemAtPosition(i, j)
                if wid is not None:
                    self.layout.removeWidget(wid)
                    wid.deleteLater()
                    wid.finalize()
        self.layout.addWidget(widget, x, y, w, h)

    def setSize(self, size):
        for s in range(size):
            self.layout.setColumnStretch(s, 1)
            self.layout.setRowStretch(s, 1)

    def itemAtPosition(self, i, j):
        item = self.layout.itemAtPosition(i, j)
        if item is not None:
            return item.widget()
        else:
            return None


class _GridAttachedWindow(LysSubWindow):
    def __init__(self, title):
        super().__init__()
        self.setWindowTitle(title)
        self.grid = _MultipleGrid()
        self.grid.setSize(4)
        self.closeforce = False
        self.grid.closed.connect(self.forceclose)
        self.attach(self.grid)
        self.attachTo()
        self.adjustSize()
        self.updateGeometry()

    def forceclose(self):
        self.closeforce = True
        self.close()

    def closeEvent(self, event):
        if self.closeforce:
            event.accept()
            return super().closeEvent(event)
        else:
            self.hide()
            event.ignore()
            return

    def keyPress(self, e):
        if e.key() == QtCore.Qt.Key_M:
            self.show()


class MultiCut(_GridAttachedWindow):
    def __init__(self, wave):
        super().__init__("Multi-dimensional data analysis")
        self._cui = MultiCutCUI(wave)
        self.__initlayout__()

    def __exportTab(self):
        self._ani = AnimationTab(self._cui)
        self._data = ExportDataTab(self._cui)
        self._ani.updated.connect(self._cut.update)
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self._data)
        lay.addWidget(self._ani)
        lay.addStretch()
        w.setLayout(lay)
        return w

    def __initlayout__(self):
        self._pre = PrefilterTab(self._cui)
        self._pre.filterApplied.connect(self._cui.applyFilter)
        self._cut = CutTab(self._cui, self, self.grid)

        tab = QtWidgets.QTabWidget()
        tab.addTab(self._pre, "Prefilter")
        tab.addTab(self._cut, "Cut")
        tab.addTab(self.__exportTab(), "Export")

        self.setWidget(tab)
        self.adjustSize()
