import numpy as np

from lys.Qt import QtWidgets
from lys.widgets import ScientificSpinBox
from lys.decorators import avoidCircularReference

from .AnnotationGUI import AnnotationSelectionBox, LineColorAdjustBox, LineStyleAdjustBox


class _LinePositionAdjustBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.__initlayout()
        self.data = []

    def __initlayout(self):
        self._x1 = ScientificSpinBox(valueChanged=self._chgPos)
        self._y1 = ScientificSpinBox(valueChanged=self._chgPos)
        self._x2 = ScientificSpinBox(valueChanged=self._chgPos)
        self._y2 = ScientificSpinBox(valueChanged=self._chgPos)
        self._label = QtWidgets.QLabel()

        g = QtWidgets.QGridLayout()
        g.addWidget(QtWidgets.QLabel("Point 1"), 1, 0)
        g.addWidget(QtWidgets.QLabel("Point 2"), 2, 0)
        g.addWidget(QtWidgets.QLabel("x axis"), 0, 1)
        g.addWidget(QtWidgets.QLabel("y axis"), 0, 2)
        g.addWidget(self._x1, 1, 1)
        g.addWidget(self._y1, 1, 2)
        g.addWidget(self._x2, 2, 1)
        g.addWidget(self._y2, 2, 2)
        g.addWidget(QtWidgets.QLabel("Distance"), 3, 0)
        g.addWidget(self._label, 3, 1, 1, 2)
        g.addWidget(QtWidgets.QPushButton("Copy", clicked=self._copy), 4, 1)
        g.addWidget(QtWidgets.QPushButton("Paste", clicked=self._paste), 4, 2)

        v = QtWidgets.QVBoxLayout()
        v.addLayout(g)
        v.addStretch()

        self.setLayout(v)

    @avoidCircularReference
    def _loadstate(self, *args, **kwargs):
        if len(self.data) != 0:
            d = self.data[0]
            p1, p2 = d.getPosition()
            self._x1.setValue(p1[0])
            self._y1.setValue(p1[1])
            self._x2.setValue(p2[0])
            self._y2.setValue(p2[1])
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            txt = "dx = {:.3g}, dy = {:.3g}, d = {:.3g}".format(dx, dy, np.sqrt(dx**2 + dy**2))
            self._label.setText(txt)

    @avoidCircularReference
    def _chgPos(self, *args, **kwargs):
        if len(self.data) != 0:
            p1 = self._x1.value(), self._y1.value()
            p2 = self._x2.value(), self._y2.value()
            for d in self.data:
                d.setPosition([p1, p2])
            self._loadstate()

    def _copy(self):
        if len(self.data) != 0:
            cb = QtWidgets.QApplication.clipboard()
            cb.clear(mode=cb.Clipboard)
            cb.setText(str(self.data[0].getPosition()), mode=cb.Clipboard)

    def _paste(self):
        cb = QtWidgets.QApplication.clipboard()
        v = np.array(eval(cb.text(mode=cb.Clipboard)))
        if v.shape[0] == v.shape[1] == 2:
            for d in self.data:
                d.setPosition(v)
        self._loadstate()

    def setData(self, data):
        if len(self.data) != 0:
            self.data[0].positionChanged.disconnect(self._loadstate)
        if len(data) != 0:
            data[0].positionChanged.connect(self._loadstate)
        self.data = data
        self._loadstate()


class LineAnnotationBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

        sel = AnnotationSelectionBox(canvas, 'line')
        col = LineColorAdjustBox(canvas, 'line')
        stl = LineStyleAdjustBox(canvas, 'line')
        pos = _LinePositionAdjustBox(canvas)
        sel.selected.connect(col.setData)
        sel.selected.connect(stl.setData)
        sel.selected.connect(pos.setData)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(sel)

        lv1 = QtWidgets.QVBoxLayout()
        lv1.addWidget(QtWidgets.QLabel('Color'))
        lv1.addWidget(col)
        lv1.addWidget(stl)
        w = QtWidgets.QWidget()
        w.setLayout(lv1)

        tab = QtWidgets.QTabWidget()
        tab.addTab(pos, 'Position')
        tab.addTab(w, 'Appearance')
        layout.addWidget(tab)
        self.setLayout(layout)


class _InfiniteLinePositionAdjustBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.__initlayout()
        self.data = []

    def __initlayout(self):
        self._pos = ScientificSpinBox(valueChanged=self._chgPos)
        self._label = QtWidgets.QLabel()

        h = QtWidgets.QHBoxLayout()
        h.addWidget(QtWidgets.QLabel("Position"))
        h.addWidget(self._pos)

        v = QtWidgets.QVBoxLayout()
        v.addWidget(self._label)
        v.addLayout(h)
        v.addStretch()

        self.setLayout(v)

    @avoidCircularReference
    def _loadstate(self, *args, **kwargs):
        if len(self.data) != 0:
            d = self.data[0]
            self._pos.setValue(d.getPosition())
            self._label.setText("Direction: " + d.getOrientation())

    @avoidCircularReference
    def _chgPos(self, *args, **kwargs):
        if len(self.data) != 0:
            for d in self.data:
                d.setPosition(self._pos.value())

    def setData(self, data):
        if len(self.data) != 0:
            self.data[0].positionChanged.disconnect(self._loadstate)
        if len(data) != 0:
            data[0].positionChanged.connect(self._loadstate)
        self.data = data
        self._loadstate()


class InfiniteLineAnnotationBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

        sel = AnnotationSelectionBox(canvas, 'infiniteLine')
        col = LineColorAdjustBox(canvas, 'infiniteLine')
        stl = LineStyleAdjustBox(canvas, 'infiniteLine')
        pos = _InfiniteLinePositionAdjustBox(canvas)
        sel.selected.connect(col.setData)
        sel.selected.connect(stl.setData)
        sel.selected.connect(pos.setData)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(sel)

        lv1 = QtWidgets.QVBoxLayout()
        lv1.addWidget(QtWidgets.QLabel('Color'))
        lv1.addWidget(col)
        lv1.addWidget(stl)
        w = QtWidgets.QWidget()
        w.setLayout(lv1)

        tab = QtWidgets.QTabWidget()
        tab.addTab(pos, 'Position')
        tab.addTab(w, 'Appearance')
        layout.addWidget(tab)
        self.setLayout(layout)
