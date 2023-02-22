
from lys.Qt import QtWidgets, QtCore, QtGui
from lys.widgets import LysSubWindow

from .MultiCut import MultiCutCUI
from .MultiCutGUIs import CutTab, AnimationTab, PrefilterTab, ExportDataTab


class _MultipleGrid(LysSubWindow):
    showMulti = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.__initlayout()
        self.resize(400, 400)
        self.closed.connect(self.__finalize)

    def __finalize(self):
        for i in range(4):
            for j in range(4):
                w = self.itemAtPosition(i, j)
                if w is not None:
                    w.finalize()

    def __initlayout(self):
        self.layout = QtWidgets.QGridLayout()
        w = QtWidgets.QWidget()
        w.setLayout(self.layout)
        self._overlay = _GridOverlay(w)
        self.startSelection = self._overlay.startSelection
        self.selected = self._overlay.selected
        self.resized.connect(lambda: self._overlay.resize(w.size()))
        self.resized.connect(lambda: self._overlay.raise_())
        self.setWidget(w)

    def Append(self, widget, x, y, w, h):
        for i in range(x, x + w):
            for j in range(y, y + h):
                wid = self.itemAtPosition(i, j)
                if wid is not None:
                    self.layout.removeWidget(wid)
                    wid.deleteLater()
                    wid.finalize()
        widget.keyPressed.connect(self.keyPress)
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

    def keyPress(self, e):
        if e.key() == QtCore.Qt.Key_M:
            self.showMulti.emit()


class _GridOverlay(QtWidgets.QWidget):
    selected = QtCore.pyqtSignal(object)

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setParent(parent)
        self.setStyleSheet("background-color: transparent;")
        self.resize(parent.size())
        self.__started = False
        self.show()

    def startSelection(self):
        self.__started = True
        self.__p1 = (-1, -1)
        self.__p2 = (-1, -1)
        self.resize(self.parentWidget().size())
        self.raise_()
        self.repaint()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        if self.__started:
            b1 = QtGui.QBrush(QtGui.QColor(255, 69, 0, 128))
            b2 = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))
            for i in range(4):
                for j in range(4):
                    x = min(self.__p1[0], self.__p2[0]) <= i <= max(self.__p1[0], self.__p2[0])
                    y = min(self.__p1[1], self.__p2[1]) <= j <= max(self.__p1[1], self.__p2[1])
                    painter.drawRect(self.width() / 4 * i, self.height() / 4 * j, self.width() / 4 * (i + 1), self.height() / 4 * (j + 1))
                    painter.fillRect(self.width() / 4 * i, self.height() / 4 * j, self.width() / 4, self.height() / 4, b1 if x and y else b2)

    def __calcPosition(self, event):
        x, y = event.x(), event.y()
        return int(x / (self.width() / 4)), int(y / (self.height() / 4))

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.__started = False
        print(self.__p1, self.__p2)
        self.selected.emit((self.__p1, self.__p2))
        self.lower()
        self.repaint()

    def mousePressEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.__started:
            self.__p1 = self.__calcPosition(event)

    def mouseMoveEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.__started:
            self.__p2 = self.__calcPosition(event)
            self.repaint()


class _GridAttachedWindow(LysSubWindow):
    def __init__(self, title):
        super().__init__()
        self.setWindowTitle(title)
        self.grid = _MultipleGrid()
        self.grid.setSize(4)
        self.grid.showMulti.connect(self.show)
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
        self._cut = CutTab(self._cui, self.grid)

        tab = QtWidgets.QTabWidget()
        tab.addTab(self._pre, "Prefilter")
        tab.addTab(self._cut, "Cut")
        tab.addTab(self.__exportTab(), "Export")

        self.setWidget(tab)
        self.adjustSize()
