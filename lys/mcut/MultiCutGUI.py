
from lys.Qt import QtWidgets, QtCore, QtGui
from lys.widgets import LysSubWindow, CanvasBase

from .MultiCutCUI import MultiCutCUI
from .CanvasManager import CanvasManager
from .MultiCutGUIs import CutTab, AnimationTab, PrefilterTab, ExportDataTab


class _MultipleGrid(LysSubWindow):
    showMulti = QtCore.pyqtSignal()

    def __init__(self, size=4):
        super().__init__()
        self.__initlayout()
        self.setSize(size)
        self.__widget = None
        self.__supressCancel = False
        self.resize(400, 400)
        self.closed.connect(self.__finalize)

    def __finalize(self):
        for w in self.widgets():
            w.finalize()

    def __initlayout(self):
        self.layout = QtWidgets.QGridLayout()
        w = QtWidgets.QWidget()
        w.setLayout(self.layout)
        self._overlay = _GridOverlay(w)
        self._overlay.selected.connect(self._selected)
        self._overlay.canceled.connect(self._canceled)
        self.resized.connect(lambda: self._overlay.resize(w.size()))
        self.setWidget(w)
        self.installEventFilter(self)

    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.FocusOut:
            if self.__supressCancel:
                self.__supressCancel = False
            else:
                self._canceled()
        return super().eventFilter(object, event)

    def __startSelection(self):
        for w in self.widgets():
            w.setFocusPolicy(QtCore.Qt.NoFocus)
        self.raise_()
        self._overlay.startSelection()
        self.setFocus()

    def append(self, widget, pos=None, wid=None):
        if pos is None or wid is None:
            self.__widget = widget
            self.__startSelection()
            return
        for i in range(pos[0], pos[0] + wid[0]):
            for j in range(pos[1], pos[1] + wid[1]):
                self.remove(i, j)
        self.layout.addWidget(widget, pos[0], pos[1], wid[0], wid[1])
        widget.keyPressed.connect(self.__keyPress)
        self.__widget = None

    def remove(self, row, column):
        w = self.itemAtPosition(row, column)
        if w is not None:
            self.layout.removeWidget(w)
            w.deleteLater()
            if isinstance(w, CanvasBase):
                w.finalize()

    def _selected(self, obj):
        pos, end = obj
        wid = end[0] - pos[0] + 1, end[1] - pos[1] + 1
        for w in self.widgets():
            w.setFocusPolicy(QtCore.Qt.StrongFocus)
        if self.__checkItem(pos, wid):
            self.__supressCancel = True
            msgBox = QtWidgets.QMessageBox(parent=self, text="There is a graph at this position. Do you really want to proceed?")
            msgBox.addButton(QtWidgets.QMessageBox.Yes)
            no = msgBox.addButton(QtWidgets.QMessageBox.No)
            cancel = msgBox.addButton(QtWidgets.QMessageBox.Cancel)
            msgBox.exec_()
            if msgBox.clickedButton() == no:
                return self._canceled()
            elif msgBox.clickedButton() == cancel:
                self.__supressCancel = True
                return self.__startSelection()
        self._overlay.lower()
        self.append(self.__widget, pos, wid)

    def __checkItem(self, pos, wid):
        for i in range(pos[0], pos[0] + wid[0]):
            for j in range(pos[1], pos[1] + wid[1]):
                if self.itemAtPosition(i, j) is not None:
                    return True
        return False

    def _canceled(self):
        if self.__widget is not None:
            self.__widget.finalize()
            self.__widget = None
            self._overlay.stopSelection()
            self._overlay.lower()

    def __keyPress(self, e):
        if e.key() == QtCore.Qt.Key_M:
            self.showMulti.emit()

    def setSize(self, size):
        self.__size = size
        for s in range(size):
            self.layout.setColumnStretch(s, 1)
            self.layout.setRowStretch(s, 1)

    def itemAtPosition(self, i, j):
        item = self.layout.itemAtPosition(i, j)
        if item is not None:
            return item.widget()
        else:
            return None

    def widgets(self):
        wids = []
        for i in range(self.__size):
            for j in range(self.__size):
                item = self.itemAtPosition(i, j)
                if item not in wids and item is not None:
                    wids.append(item)
        return wids


class _GridOverlay(QtWidgets.QWidget):
    selected = QtCore.pyqtSignal(object)
    canceled = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setParent(parent)
        self.setStyleSheet("background-color: transparent;")
        self.resize(parent.size())
        self.__started = False
        self.__paint = False
        self.show()

    def startSelection(self):
        self.raise_()
        self.__started = True
        self.__paint = True
        self.__p1 = (-1, -1)
        self.__p2 = (-1, -1)
        self.resize(self.parentWidget().size())
        self.repaint()

    def stopSelection(self):
        self.__started = False
        self.__paint = False
        self.repaint()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        if self.__paint:
            c1 = QtGui.QBrush(QtGui.QColor(255, 69, 0, 128))
            c2 = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            for i in range(4):
                for j in range(4):
                    x = min(self.__p1[0], self.__p2[0]) <= i <= max(self.__p1[0], self.__p2[0])
                    y = min(self.__p1[1], self.__p2[1]) <= j <= max(self.__p1[1], self.__p2[1])
                    painter.setBrush(c1 if x and y else c2)
                    painter.drawRect(self.width() / 4.0 * i, self.height() / 4.0 * j, self.width() / 4.0, self.height() / 4.0)

    def __calcPosition(self, event):
        x, y = event.x(), event.y()
        return int(x / (self.width() / 4)), int(y / (self.height() / 4))

    def mouseReleaseEvent(self, event):
        if self.__started:
            self.__started = False
            p1 = min(self.__p1[1], self.__p2[1]), min(self.__p1[0], self.__p2[0])
            p2 = max(self.__p1[1], self.__p2[1]), max(self.__p1[0], self.__p2[0])
            self.selected.emit((p1, p2))
            if not self.__started:
                self.__paint = False
            self.repaint()
        return super().mouseReleaseEvent(event)

    def mousePressEvent(self, event):
        if self.__started:
            self.__p1 = self.__calcPosition(event)
            self.__p2 = self.__calcPosition(event)
        return super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.__started:
            self.__p2 = self.__calcPosition(event)
            self.repaint()
        return super().mouseReleaseEvent(event)


class _GridAttachedWindow(LysSubWindow):
    def __init__(self, title):
        super().__init__()
        self.setWindowTitle(title)
        self.grid = _MultipleGrid()
        self.grid.showMulti.connect(self.show)
        self.closeforce = False
        self.grid.closed.connect(self.forceclose)
        self.attach(self.grid)
        self.attachTo()

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
        self._can = CanvasManager(self._cui)
        self.__initlayout__()

    def __getattr__(self, key):
        if "_can" in self.__dict__:
            if hasattr(self._can, key):
                return getattr(self._can, key)
        return super().__getattr__(key)

    def __exportTab(self):
        self._ani = AnimationTab(self._cui)
        self._data = ExportDataTab(self._cui)
        self._ani.updated.connect(self._cut.update)

        lay = QtWidgets.QVBoxLayout()
        lay.addWidget(self._data)
        lay.addWidget(self._ani)
        lay.addStretch()

        w = QtWidgets.QWidget()
        w.setLayout(lay)
        return w

    def __initlayout__(self):
        self._pre = PrefilterTab(self._cui)
        self._pre.filterApplied.connect(self._cui.applyFilter)
        self._cut = CutTab(self._cui, self)

        tab = QtWidgets.QTabWidget()
        tab.addTab(self._pre, "Prefilter")
        tab.addTab(self._cut, "Cut")
        tab.addTab(self.__exportTab(), "Export")

        self.setWidget(tab)
        self.adjustSize()
        self.updateGeometry()

    def display(self, wave, type="grid", pos=None, wid=None):
        if type == "graph":
            c = self._can.createCanvas(wave.getAxes(), graph=True)
        else:
            c = self._can.createCanvas(wave.getAxes(), lib="pyqtgraph")
            self.grid.append(c, pos, wid)
        c.Append(wave.getFilteredWave())
        return c

    @property
    def cui(self):
        return self._cui
