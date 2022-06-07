import numpy as np

from lys.Qt import QtWidgets
from lys.widgets import ScientificSpinBox
from lys.decorators import avoidCircularReference

from .AnnotationGUI import AnnotationSelectionBox, LineColorAdjustBox, LineStyleAdjustBox


class _RectPositionAdjustBox(QtWidgets.QWidget):
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
            p1, p2 = d.getRegion()
            self._x1.setValue(p1[0])
            self._y1.setValue(p2[0])
            self._x2.setValue(p1[1])
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
                d.setRegion(np.array([p1, p2]).T)
            self._loadstate()

    def _copy(self):
        if len(self.data) != 0:
            cb = QtWidgets.QApplication.clipboard()
            cb.clear(mode=cb.Clipboard)
            cb.setText(str(self.data[0].getRegion()), mode=cb.Clipboard)

    def _paste(self):
        cb = QtWidgets.QApplication.clipboard()
        v = np.array(eval(cb.text(mode=cb.Clipboard)))
        if v.shape[0] == v.shape[1] == 2:
            for d in self.data:
                d.setRegion(v)
        self._loadstate()

    def setData(self, data):
        if len(self.data) != 0:
            self.data[0].regionChanged.disconnect(self._loadstate)
        if len(data) != 0:
            data[0].regionChanged.connect(self._loadstate)
        self.data = data
        self._loadstate()


class RectAnnotationBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

        sel = AnnotationSelectionBox(canvas, 'rect')
        lcol = LineColorAdjustBox(canvas, 'rect')
        lsty = LineStyleAdjustBox(canvas, 'rect')
        pos = _RectPositionAdjustBox(canvas)

        sel.selected.connect(lcol.setData)
        sel.selected.connect(lsty.setData)
        sel.selected.connect(pos.setData)

        lv1 = QtWidgets.QVBoxLayout()
        lv1.addWidget(lcol)
        lv1.addWidget(lsty)
        lv1.addStretch()

        w = QtWidgets.QWidget()
        w.setLayout(lv1)

        tab = QtWidgets.QTabWidget()
        tab.addTab(pos, 'Position')
        tab.addTab(w, 'Appearance')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(sel)
        layout.addWidget(tab)
        self.setLayout(layout)


class _RegionPositionAdjustBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.__initlayout()
        self.data = []

    def __initlayout(self):
        self._x1 = ScientificSpinBox(valueChanged=self._chgPos)
        self._x2 = ScientificSpinBox(valueChanged=self._chgPos)
        self._label = QtWidgets.QLabel()

        g = QtWidgets.QGridLayout()
        g.addWidget(QtWidgets.QLabel("Point 1"), 0, 0)
        g.addWidget(QtWidgets.QLabel("Point 2"), 1, 0)
        g.addWidget(self._x1, 0, 1, 1, 2)
        g.addWidget(self._x2, 1, 1, 1, 2)
        g.addWidget(QtWidgets.QPushButton("Copy", clicked=self._copy), 2, 1)
        g.addWidget(QtWidgets.QPushButton("Paste", clicked=self._paste), 2, 2)

        v = QtWidgets.QVBoxLayout()
        v.addWidget(self._label)
        v.addLayout(g)
        v.addStretch()
        self.setLayout(v)

    @avoidCircularReference
    def _loadstate(self, *args, **kwargs):
        if len(self.data) != 0:
            d = self.data[0]
            self._label.setText("Orientation: " + d.getOrientation())
            p1, p2 = d.getRegion()
            self._x1.setValue(p1)
            self._x2.setValue(p2)

    @avoidCircularReference
    def _chgPos(self, *args, **kwargs):
        if len(self.data) != 0:
            r = self._x1.value(), self._x2.value()
            for d in self.data:
                d.setRegion(r)
            self._loadstate()

    def _copy(self):
        if len(self.data) != 0:
            cb = QtWidgets.QApplication.clipboard()
            cb.clear(mode=cb.Clipboard)
            cb.setText(str(self.data[0].getRegion()), mode=cb.Clipboard)

    def _paste(self):
        cb = QtWidgets.QApplication.clipboard()
        v = np.array(eval(cb.text(mode=cb.Clipboard)))
        if v.shape[0] == 2:
            for d in self.data:
                d.setRegion(v)
        self._loadstate()

    def setData(self, data):
        if len(self.data) != 0:
            self.data[0].regionChanged.disconnect(self._loadstate)
        if len(data) != 0:
            data[0].regionChanged.connect(self._loadstate)
        self.data = data
        self._loadstate()


class RegionAnnotationBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

        sel = AnnotationSelectionBox(canvas, 'region')
        lcol = LineColorAdjustBox(canvas, 'region')
        lsty = LineStyleAdjustBox(canvas, 'region')
        pos = _RegionPositionAdjustBox(canvas)

        sel.selected.connect(lcol.setData)
        sel.selected.connect(lsty.setData)
        sel.selected.connect(pos.setData)

        lv1 = QtWidgets.QVBoxLayout()
        lv1.addWidget(lcol)
        lv1.addWidget(lsty)
        lv1.addStretch()

        w = QtWidgets.QWidget()
        w.setLayout(lv1)

        tab = QtWidgets.QTabWidget()
        tab.addTab(pos, 'Position')
        tab.addTab(w, 'Appearance')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(sel)
        layout.addWidget(tab)
        self.setLayout(layout)


class _FreeRegionPositionAdjustBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.__initlayout()
        self.data = []

    def __initlayout(self):
        self._x1 = ScientificSpinBox(valueChanged=self._chgPos)
        self._y1 = ScientificSpinBox(valueChanged=self._chgPos)
        self._x2 = ScientificSpinBox(valueChanged=self._chgPos)
        self._y2 = ScientificSpinBox(valueChanged=self._chgPos)
        self._wid = ScientificSpinBox(valueChanged=self._chgPos)
        self._label = QtWidgets.QLabel()

        g = QtWidgets.QGridLayout()
        g.addWidget(QtWidgets.QLabel("Point 1"), 1, 0)
        g.addWidget(QtWidgets.QLabel("Point 2"), 2, 0)
        g.addWidget(QtWidgets.QLabel("Width"), 3, 0)
        g.addWidget(QtWidgets.QLabel("x axis"), 0, 1)
        g.addWidget(QtWidgets.QLabel("y axis"), 0, 2)
        g.addWidget(self._x1, 1, 1)
        g.addWidget(self._y1, 1, 2)
        g.addWidget(self._x2, 2, 1)
        g.addWidget(self._y2, 2, 2)
        g.addWidget(self._wid, 3, 1, 1, 2)
        g.addWidget(QtWidgets.QLabel("Distance"), 4, 0)
        g.addWidget(self._label, 4, 1, 1, 2)
        g.addWidget(QtWidgets.QPushButton("Copy", clicked=self._copy), 5, 1)
        g.addWidget(QtWidgets.QPushButton("Paste", clicked=self._paste), 5, 2)

        v = QtWidgets.QVBoxLayout()
        v.addLayout(g)
        v.addStretch()

        self.setLayout(v)

    @avoidCircularReference
    def _loadstate(self, *args, **kwargs):
        if len(self.data) != 0:
            d = self.data[0]
            p1, p2 = d.getRegion()
            self._x1.setValue(p1[0])
            self._y1.setValue(p1[1])
            self._x2.setValue(p2[0])
            self._y2.setValue(p2[1])
            self._wid.setValue(d.getWidth())
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            txt = "dx = {:.3g}, dy = {:.3g}, d = {:.3g}".format(dx, dy, np.sqrt(dx**2 + dy**2))
            self._label.setText(txt)

    @avoidCircularReference
    def _chgPos(self, *args, **kwargs):
        if len(self.data) != 0:
            p1 = self._x1.value(), self._y1.value()
            p2 = self._x2.value(), self._y2.value()
            w = self._wid.value()
            for d in self.data:
                d.setRegion([p1, p2])
                d.setWidth(w)
            self._loadstate()

    def _copy(self):
        if len(self.data) != 0:
            cb = QtWidgets.QApplication.clipboard()
            cb.clear(mode=cb.Clipboard)
            cb.setText(str((self.data[0].getRegion(), self.data[0].getWidth())), mode=cb.Clipboard)

    def _paste(self):
        cb = QtWidgets.QApplication.clipboard()
        val = eval(cb.text(mode=cb.Clipboard))
        v, w = np.array(val[0]), val[1]
        if v.shape[0] == v.shape[1] == 2:
            for d in self.data:
                d.setRegion(v)
                d.setWidth(w)
        self._loadstate()

    def setData(self, data):
        if len(self.data) != 0:
            self.data[0].regionChanged.disconnect(self._loadstate)
        if len(data) != 0:
            data[0].regionChanged.connect(self._loadstate)
        self.data = data
        self._loadstate()


class FreeRegionAnnotationBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

        sel = AnnotationSelectionBox(canvas, 'freeRegion')
        lcol = LineColorAdjustBox(canvas, 'freeRegion')
        lsty = LineStyleAdjustBox(canvas, 'freeRegion')
        pos = _FreeRegionPositionAdjustBox(canvas)

        sel.selected.connect(lcol.setData)
        sel.selected.connect(lsty.setData)
        sel.selected.connect(pos.setData)

        lv1 = QtWidgets.QVBoxLayout()
        lv1.addWidget(lcol)
        lv1.addWidget(lsty)
        lv1.addStretch()

        w = QtWidgets.QWidget()
        w.setLayout(lv1)

        tab = QtWidgets.QTabWidget()
        tab.addTab(pos, 'Position')
        tab.addTab(w, 'Appearance')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(sel)
        layout.addWidget(tab)
        self.setLayout(layout)
