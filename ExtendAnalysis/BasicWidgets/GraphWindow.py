#!/usr/bin/env python
import random
import sys
import os
from enum import Enum
from PyQt5.QtGui import *

from ExtendAnalysis import registerFileLoader
from ExtendAnalysis.widgets import AutoSavedWindow
from .Commons.ExtendTable import *
from .ModifyWindow.ModifyWindow import *
from .FittingWindow import *


class Graph(AutoSavedWindow):
    graphLibrary = "matplotlib"

    @classmethod
    def active(cls, n=0, exclude=None):
        list = LysMdiArea.current().subWindowList(order=QMdiArea.ActivationHistoryOrder)
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
        list = LysMdiArea.current().subWindowList(order=QMdiArea.ActivationHistoryOrder)
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
        if file is not None:
            self._load(file)
        self.canvas.keyPressed.connect(self.keyPress)
        self.closed.connect(self.canvas.emitCloseEvent)
        self.resized.connect(self.canvas.parentResized)
        self.canvas.setSaveFunction(self.Save)
        if file is not None:
            self.canvas.RestoreSize()
        else:
            self.canvas.RestoreSize(init=True)

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

    def Append(self, wave, axis=Axis.BottomLeft, contour=False, vector=False):
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
    return append(*args, graph=g)


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


class PreviewWindow(LysSubWindow):
    instance = None

    def __new__(cls, list):
        if cls.__checkInstance():
            return cls.instance()
        return LysSubWindow.__new__(cls)

    @classmethod
    def __checkInstance(cls):
        if cls.instance is not None:
            if cls.instance() is not None:
                return True
        return False

    def __init__(self, list):
        if self.__checkInstance():
            self.main.Clear()
            self.left.Clear()
            self.bottom.Clear()
        else:
            PreviewWindow.instance = weakref.ref(self)
            super().__init__()
            self.setWindowTitle("Preview Window")
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.resize(500, 500)
            self.updateGeometry()
            self.__initcanvas()
            self.__initlayout()
        n = 1
        if hasattr(list, '__iter__'):
            lists = list
        else:
            lists = [list]
        if not len(lists) == 0:
            self.wave = lists[0]
        else:
            self.wave = None
        for l in lists:
            self.main.Append(l)
            n = max(n, l.data.ndim)
        self.dim = n
        self._setLayout(1)
        self.axis_c()
        self.show()

    def __initcanvas(self):
        self.left = ExtendCanvas()
        self.left.axisRangeChanged.connect(self.axis_l)
        self.main = ExtendCanvas()
        self.main.axisRangeChanged.connect(self.axis_c)
        self.main.addAnchorChangedListener(self.OnAnchorChanged)
        self.bottom = ExtendCanvas()
        self.bottom.axisRangeChanged.connect(self.axis_b)
        self.axisflg = False

    def __initlayout(self):
        layout = QGridLayout()
        layout.setSpacing(0)
        layout.addWidget(self.left, 0, 0)
        layout.addWidget(self.main, 0, 1)
        layout.addWidget(self.bottom, 1, 1)

        layout.setRowStretch(0, 6)
        layout.setRowStretch(1, 4)
        layout.setColumnStretch(0, 4)
        layout.setColumnStretch(1, 6)
        self.gl = layout
        wid = QWidget(self)
        wid.setLayout(layout)
        self.setWidget(wid)

    def _setLayout(self, mode):
        if mode == 2:
            self.gl.setRowStretch(0, 6)
            self.gl.setRowStretch(1, 4)
            self.gl.setColumnStretch(0, 4)
            self.gl.setColumnStretch(1, 6)
            self.left.show()
            self.bottom.show()
        elif mode == 1:
            self.gl.setRowStretch(0, 6)
            self.gl.setRowStretch(1, 0)
            self.gl.setColumnStretch(0, 0)
            self.gl.setColumnStretch(1, 6)
            self.left.hide()
            self.bottom.hide()

    def axis_l(self):
        if self.axisflg:
            return
        self.axisflg = True
        range = self.left.getAxisRange('Left')
        self.main.setAxisRange(range, 'Left')
        self.axisflg = False

    def axis_b(self):
        if self.axisflg:
            return
        self.axisflg = True
        range = self.bottom.getAxisRange('Bottom')
        self.main.setAxisRange(range, 'Bottom')
        self.axisflg = False

    def axis_c(self):
        if self.axisflg:
            return
        self.axisflg = True
        range = self.main.getAxisRange('Left')
        self.left.setAxisRange(range, 'Left')
        range = self.main.getAxisRange('Bottom')
        self.bottom.setAxisRange(range, 'Bottom')
        self.axisflg = False

    def OnAnchorChanged(self):
        print("anchor is deprecated.")
        self.left.Clear()
        self.bottom.Clear()
        flg = False
        for i in [1, 2, 3]:
            res = self.main.getAnchorInfo(i)
            if res is None:
                continue
            w = res[0]
            if w is None:
                continue
            if w.wave.data.ndim == 2:
                flg = True
                p = w.wave.posToPoint(res[1])
                slicex = Wave()
                slicex.data = w.wave.data[p[1], :]
                slicex.x = w.wave.x
                slicey = Wave()
                slicey.data = w.wave.y
                slicey.x = w.wave.data[:, p[0]]
                id1 = self.left.Append(slicey)
                id2 = self.bottom.Append(slicex)
                self.left.setDataColor(self.main.getAnchorColor(i), id1)
                self.bottom.setDataColor(self.main.getAnchorColor(i), id2)
        anc1 = self.main.getAnchorInfo(1)
        anc2 = self.main.getAnchorInfo(2)
        if anc1 is not None and anc2 is not None:
            if anc1[0] == anc2[0]:
                flg = True
                w = anc1[0].wave
                p1 = w.posToPoint(anc1[1])
                p2 = w.posToPoint(anc2[1])
                slicex = w.slice(p1, p2, 'x')
                slicey = w.slice(p1, p2, 'y')
                id1 = self.left.Append(slicey)
                id2 = self.bottom.Append(slicex)
                self.left.setDataColor(self.main.getAnchorColor(i), id1)
                self.bottom.setDataColor(self.main.getAnchorColor(i), id2)
        if flg:
            self._setLayout(2)
        else:
            self._setLayout(1)

    @classmethod
    def SelectedArea(cls):
        if not cls.__checkInstance():
            return None
        obj = cls.instance()
        if obj.wave == None:
            return None
        pt = obj.main.SelectedRange()
        if pt is None:
            return None
        return (obj.wave.posToPoint(pt[0]), obj.wave.posToPoint(pt[1]))

    @classmethod
    def AnchorArea(cls):
        if not cls.__checkInstance():
            return None
        obj = cls.instance()
        if obj.wave == None:
            return None
        anc1 = obj.main.getAnchorInfo(1)
        anc2 = obj.main.getAnchorInfo(2)
        if anc1 is not None and anc2 is not None:
            if anc1[0] == anc2[0]:
                return (obj.wave.posToPoint(anc1[1]), obj.wave.posToPoint(anc2[1]))


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
