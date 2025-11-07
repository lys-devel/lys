
from lys import resources
from lys.Qt import QtWidgets, QtCore, QtGui
from lys.widgets import LysSubWindow, CanvasBase, canvas

from .MultiCutCUI import MultiCutCUI
from .CanvasManager import CanvasManager


class _MultiCutWindow(LysSubWindow):
    """
    This is the main GUI window of MultiCut.

    It contains a grid for displaying canvases and a side bar for managing filters, axes ranges, free lines, and child waves.
    """
    def __init__(self, grid):
        super().__init__()
        self.resized.connect(lambda: grid._overlay.resize(self.size()))
        self.setWidget(grid)
        self.resize(400, 400)


class _MultipleGrid(QtWidgets.QWidget):
    showMulti = QtCore.pyqtSignal()
    closed = QtCore.pyqtSignal(object)
    focused = QtCore.pyqtSignal()

    def __init__(self, size=4):
        super().__init__()
        self.__initlayout()
        self.setSize(size)
        self.__widget = None
        self.__supressCancel = False
        self.closed.connect(self.__finalize)

    def closeEvent(self, event):
        self.closed.emit(self)
        return super().closeEvent(event)

    def __finalize(self):
        for w in self.widgets():
            w.finalize()

    def __initlayout(self):
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self._overlay = _GridOverlay(self)
        self._overlay.selected.connect(self._selected)
        self._overlay.canceled.connect(self._canceled)
        self.installEventFilter(self)

    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.FocusOut:
            if self.__supressCancel:
                self.__supressCancel = False
            else:
                self._canceled()
        if event.type() == QtCore.QEvent.FocusIn:
            self.focused.emit()
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

    def getCanvasPosition(self, w):
        index = self.layout.indexOf(w)
        return self.layout.getItemPosition(index)


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
                    painter.drawRect(int(self.width() / 4.0 * i), int(self.height() / 4.0 * j), int(self.width() / 4.0), int(self.height() / 4.0))

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


class MultiCut(QtCore.QObject):
    """
    This is central class of MultiCut.

    Although MultiCut is mainly GUI interface, it is also possible to manipulate it programatically through methods.

    Filters, axes ranges, free lines, child waves are controlled via :class:`MultiCutCUI` via *cui* property.

    Canvases in grid and independent Graphs are added by :meth:`display` method of this class.

    After adding the canvases, they are managed by :class:`CanvasManager` class.

    :class:`CanvasManager` also manages interactive annotations in the canvas.
    """
    closed = QtCore.pyqtSignal(object)
    """
    Emited when the MultiCut window is closed.
    """
    _colors = ["darkgreen", "darkred", "blue", "brown", "darkolivegreen", "dodgerblue", "indigo", "forestgreen", "mediumvioletred"]
    _colorIndex = 0

    def __init__(self, wave, subWindow=True):
        super().__init__()
        self._grid = _MultipleGrid()
        self._color = QtGui.QColor(self._colors[MultiCut._colorIndex % len(self._colors)])
        if subWindow:
            self._window = _MultiCutWindow(self._grid)
            self._window.setWindowTitle("Multicut: Multi-dimensional data analysis")
            self._window.setTitleColor(self._color)
        self._grid.focused.connect(self.openMultiCutSetting)
        self._grid.closed.connect(self.__onClose)
        self._cui = MultiCutCUI(wave)
        self._can = CanvasManager(self._cui, self._color)
        MultiCut._colorIndex += 1
        self._cui.dimensionChanged.connect(self._can.clear)
        self.openMultiCutSetting()

    def __onClose(self):
        self.closed.emit(self)

    def openMultiCutSetting(self):
        """
        Open multicut setting window in side bar.
        """
        from lys import glb
        glb.editMulticut(self)

    def __getattr__(self, key):
        if "_can" in self.__dict__:
            if hasattr(self._can, key):
                return getattr(self._can, key)
        return super().__getattr__(key)

    def display(self, wave, type="grid", pos=None, wid=None, **kwargs):
        """
        Display wave data created by addWave method of cui.

        Args:
            wave(_ChildWave): The child wave data created by addWave method of cui.
            type('grid' or 'graph'): Specifi the wave is displayed in grid or independent graph.
            pos(length 2 sequence): The position in the grid where the wave is displayed. If type is 'graph', it is ignored.
            wid(length 2 sequence): The width of the graph displayed in grid. If type is 'graph', it is ignored.
        """
        if type == "graph":
            c = self._can.createCanvas(wave.getAxes(), graph=True)
        else:
            c = self._can.createCanvas(wave.getAxes(), lib="pyqtgraph")
            self._grid.append(c, pos, wid)
        c.clicked.connect(self.openMultiCutSetting)
        c.Append(wave.getFilteredWave(), **kwargs)
        return c

    def saveAsDictionary(self, **kwargs):
        """
        Save the present state as dictionary.
        """
        return {"cui": self.cui.saveAsDictionary(**kwargs), "gui": self.__saveCanvas(**kwargs)}

    def loadFromDictionary(self, d, **kwargs):
        """
        Load the present state from dictionary.
        """
        self.cui.loadFromDictionary(d.get("cui", {}), **kwargs)
        self.__loadCanvas(d.get("gui", {}), **kwargs)

    def loadDefaultTemplate(self):
        """
        Load default template for the current filtered wave.
        Call this method soon after the GUI is initialized when you want to initialize the multicut widget with default template.

        Returns:
            dict: the dictionary that contains the default template parameters.
        """
        d = resources.loadDefaultTemplate(len(self._cui.getFilteredWave().shape))
        if d is not None:
            self.loadFromDictionary(d, useGrid=True, useAnnot=True)


    @property
    def cui(self):
        """
        MultiCutCUI class that manages filters, axes ranges, free lines, child waves.
        """
        return self._cui

    @property
    def widget(self):
        """
        Get the widget associated with the MultiCut instance.
        """
        return self._grid

    def __saveCanvas(self, useGrid=False, useGraph=False, useAnnot=False, **kwargs):
        d = {}
        if useGraph:
            d["Graphs"] = [self.__canvasDict(c, False, useAnnot) for c in self._can if c not in self._grid.widgets()]
        if useGrid:
            d["Grids"] = [self.__canvasDict(c, True, useAnnot) for c in self._grid.widgets()]
        return d

    def __canvasDict(self, c, grid, useAnnot):
        waves = self._cui.getChildWaves()
        d = {"axes": c._maxes}
        if grid:
            d["position"] = self._grid.getCanvasPosition(c)
        if useAnnot:
            d["annotations"] = self._can.getAnnotations(c)
        res = []
        for wd in c.getWaveData():
            for i, w in enumerate(waves):
                if w.getFilteredWave() == wd.getWave():
                    res.append({"index": i, "vector": isinstance(wd, canvas.interface.VectorData), "contour": isinstance(wd, canvas.interface.ContourData)})
        d["waves"] = res
        return d

    def __loadCanvas(self, dic, useGrid=False, useGraph=False, useAnnot=False, useLine=False, useRange=False, axesMap=None, **kwargs):
        self._can.clear()
        if useGraph:
            for d in dic.get("Graphs", []):
                self.__canvasFromDict(d, useAnnot, useLine, useRange, axesMap)
        if useGrid:
            for d in dic.get("Grids", []):
                self.__canvasFromDict(d, useAnnot, useLine, useRange, axesMap)

    def __canvasFromDict(self, d, useAnnot, useLine, useRange, axesMap):
        isGrid = "position" in d
        if axesMap is not None:
            d["axes"] = [axesMap[ax] if ax in axesMap else ax for ax in d["axes"]]
        if isGrid:
            c = self.createCanvas(d["axes"], graph=False, lib="pyqtgraph")
            pos = d["position"]
            self._grid.append(c, (pos[0], pos[1]), (pos[2], pos[3]))
        else:
            c = self.createCanvas(d["axes"], graph=True)
        c.clicked.connect(self.openMultiCutSetting)
        waves = self._cui.getChildWaves()
        for data in d.get("waves", []):
            w = waves[data["index"]]
            c.Append(w.getFilteredWave(), vector=data["vector"], contour=data["contour"])
        if useAnnot:
            self._can.addAnnotations(c, d.get("annotations", []), useLine, overwrite=not useRange)
