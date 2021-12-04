#!/usr/bin/env python
import os
from LysQt.QtGui import *

from lys import registerFileLoader
from lys.widgets import AutoSavedWindow, _ExtendMdiArea
from .Commons.ExtendTable import *
from .ModifyWindow.ModifyWindow import *
from .FittingWindow import *


class Graph(AutoSavedWindow):
    graphLibrary = "matplotlib"

    @classmethod
    def active(cls, n=0, exclude=None):
        list = _ExtendMdiArea.current().subWindowList(order=QMdiArea.ActivationHistoryOrder)
        m = 0
        for l in reversed(list):
            if isinstance(l, Graph):
                if exclude == l or exclude == l.canvas:
                    continue
                if m == n:
                    return l
                else:
                    m += 1

    @classmethod
    def closeAllGraphs(cls):
        list = _ExtendMdiArea.current().subWindowList(order=QMdiArea.ActivationHistoryOrder)
        for l in reversed(list):
            if isinstance(l, Graph):
                l.close(force=True)

    def _prefix(self):
        return 'graph'

    def _suffix(self):
        return '.grf'

    def __init__(self, file=None, lib=None, **kwargs):
        super().__init__(file, **kwargs)
        if file is not None:
            lib = self._loadLibType(file)
        if lib is None:
            lib = Graph.graphLibrary
        if lib == "matplotlib":
            self.canvas = ExtendCanvas()
        elif lib == "pyqtgraph":
            self.canvas = pyqtCanvas()
        self.setWidget(self.canvas)
        self.canvas.show()
        self.canvas.canvasResized.connect(self._resizeCanvas)
        self.canvas.keyPressed.connect(self.keyPress)
        self.closed.connect(self.canvas.emitCloseEvent)
        self.resized.connect(self.canvas.parentResized)
        self.canvas.setSaveFunction(self.Save)
        if file is not None:
            self._load(file)
        else:
            self.canvas.setCanvasSize("Both", "Auto", 4)

    def _save(self, file):
        d = {}
        if isinstance(self.canvas, ExtendCanvas):
            d['Library'] = 'matplotlib'
        elif isinstance(self.canvas, pyqtCanvas):
            d['Library'] = 'pyqtgraph'
        self.canvas.SaveAsDictionary(d, os.path.dirname(file))
        d['Graph'] = {}
        d['Graph']['Position_x'] = self.pos().x()
        d['Graph']['Position_y'] = self.pos().y()
        with open(file, 'w') as f:
            f.write(str(d))

    def _load(self, file):
        with open(file, 'r') as f:
            d = eval(f.read())
        self.move(d['Graph']['Position_x'], d['Graph']['Position_y'])
        self.canvas.LoadFromDictionary(d, os.path.dirname(file))

    def _loadLibType(self, file):
        with open(file, 'r') as f:
            d = eval(f.read())
        if 'Library' in d:
            return d["Library"]
        else:
            return "matplotlib"

    def _resizeCanvas(self, canvas):
        self.setWidth(0)
        self.setHeight(0)
        self.adjustSize()
        wmode = canvas.getSizeParams('Width')['mode']
        hmode = canvas.getSizeParams('Height')['mode']
        if wmode in ["Absolute", "Per Unit"]:
            self.setWidth(self.width())
        elif wmode in ["Plan", "Aspect"] and hmode in ["Absolute", "Per Unit"]:
            self.setWidth(self.width())
        if hmode in ["Absolute", "Per Unit"]:
            self.setHeight(self.height())
        elif hmode in ["Plan", "Aspect"] and wmode in ["Absolute", "Per Unit"]:
            self.setHeight(self.height())

    def keyPress(self, e):
        if e.key() == Qt.Key_G:
            ModifyWindow(self.canvas, self)
        if e.key() == Qt.Key_F:
            wavelis = []
            for d in self.canvas.getLines():
                if d.wave.FileName is not None:
                    wavelis.append(d.wave)
            FittingWindow(self, wavelis, self.canvas)
        if e.key() == Qt.Key_L:
            wavelis = []
            for d in self.canvas.getImages():
                if d.wave.FileName is not None:
                    wavelis.append(d.wave)
            LineProfileWindow(self, wavelis, self.canvas)
        if e.key() == Qt.Key_S:
            text, ok = QInputDialog.getText(self, '---Save Dialog---', 'Enter graph name:')
            if not text.endswith('.grf'):
                text += '.grf'
            if ok:
                self.Save(text)
        if e.key() == Qt.Key_D:
            #text, ok = QInputDialog.getText(self, '---Save Dialog---', 'Enter graph name:')
            self.Duplicate(lib=Graph.graphLibrary)

    def closeEvent(self, event):
        self.canvas.fig.canvas = None
        super().closeEvent(event)

    def Append(self, wave, axis="BottomLeft", contour=False, vector=False):
        return self.canvas.Append(wave, axis, contour=contour, vector=vector)

    def Duplicate(self, lib=None):
        dic = {}
        self.canvas.SaveAsDictionary(dic, home())
        g = Graph(lib=lib)
        g.canvas.EnableDraw(False)
        g.canvas.LoadFromDictionary(dic, home())
        g.canvas.EnableDraw(True)
        return g


def display(*args, lib=None, **kwargs):
    g = Graph(lib=lib)
    return append(*args, graph=g, **kwargs)


def append(*args, graph=None, **kwargs):
    if graph is None:
        g = Graph.active()
    else:
        g = graph
    for wave in args:
        if isinstance(wave, Wave):
            g.Append(wave, **kwargs)
        else:
            g.Append(Wave(wave), **kwargs)
    return g


class MultipleGrid(LysSubWindow):
    def __init__(self):
        super().__init__()
        self.__initlayout()
        self.resize(400, 400)

    def __initlayout(self):
        self.layout = QGridLayout()
        w = QWidget()
        w.setLayout(self.layout)
        self.setWidget(w)

    def Append(self, widget, x, y, w, h):
        for i in range(x, x + w):
            for j in range(y, y + h):
                wid = self.itemAtPosition(i, j)
                if wid is not None:
                    self.layout.removeWidget(wid)
                    wid.deleteLater()
                    if isinstance(wid, BasicEventCanvasBase):
                        wid.emitCloseEvent()
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


class Table(LysSubWindow):
    def __init__(self, wave=None):
        super().__init__()
        self.setWindowTitle("Table Window")
        self.resize(400, 400)
        self.__initlayout(wave)

    def __initlayout(self, wave):
        self._etable = ExtendTable(wave)
        self.setWidget(self._etable)
        self.show()

    def Append(self, wave):
        self._etable.Append(wave)

    def checkState(self, index):
        self._etable.checkState(index)

    def SetSize(self, size):
        self._etable.SetSize(size)


registerFileLoader(".grf", Graph)
