import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QGridLayout, QPushButton, QApplication

from lys.widgets import ScientificSpinBox
from lys.decorators import avoidCircularReference

from .AnnotationGUI import AnnotationSelectionBox, LineColorAdjustBox, LineStyleAdjustBox


class _RectPositionAdjustBox(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.__initlayout()
        self.data = []

    def __initlayout(self):
        self._x1 = ScientificSpinBox(valueChanged=self._chgPos)
        self._y1 = ScientificSpinBox(valueChanged=self._chgPos)
        self._x2 = ScientificSpinBox(valueChanged=self._chgPos)
        self._y2 = ScientificSpinBox(valueChanged=self._chgPos)
        self._label = QLabel()

        g = QGridLayout()
        g.addWidget(QLabel("Point 1"), 1, 0)
        g.addWidget(QLabel("Point 2"), 2, 0)
        g.addWidget(QLabel("x axis"), 0, 1)
        g.addWidget(QLabel("y axis"), 0, 2)
        g.addWidget(self._x1, 1, 1)
        g.addWidget(self._y1, 1, 2)
        g.addWidget(self._x2, 2, 1)
        g.addWidget(self._y2, 2, 2)
        g.addWidget(QLabel("Distance"), 3, 0)
        g.addWidget(self._label, 3, 1, 1, 2)
        g.addWidget(QPushButton("Copy", clicked=self._copy), 4, 1)
        g.addWidget(QPushButton("Paste", clicked=self._paste), 4, 2)

        v = QVBoxLayout()
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
            cb = QApplication.clipboard()
            cb.clear(mode=cb.Clipboard)
            cb.setText(str(self.data[0].getRegion()), mode=cb.Clipboard)

    def _paste(self):
        cb = QApplication.clipboard()
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


class RectAnnotationBox(QWidget):
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

        lv1 = QVBoxLayout()
        lv1.addWidget(lcol)
        lv1.addWidget(lsty)
        lv1.addStretch()

        w = QWidget()
        w.setLayout(lv1)

        tab = QTabWidget()
        tab.addTab(pos, 'Position')
        tab.addTab(w, 'Line')

        layout = QVBoxLayout()
        layout.addWidget(sel)
        layout.addWidget(tab)
        self.setLayout(layout)
