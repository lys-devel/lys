import numpy as np

from lys.Qt import QtWidgets
from lys.widgets import ScientificSpinBox
from lys.decorators import avoidCircularReference

from .AnnotationGUI import AnnotationSelectionBox, LineColorAdjustBox, LineStyleAdjustBox


class _CrossPositionAdjustBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.__initlayout()
        self.data = []

    def __initlayout(self):
        self._x = ScientificSpinBox(valueChanged=self._chgPos)
        self._y = ScientificSpinBox(valueChanged=self._chgPos)

        g = QtWidgets.QGridLayout()
        g.addWidget(QtWidgets.QLabel("x"), 0, 0)
        g.addWidget(QtWidgets.QLabel("y"), 1, 0)
        g.addWidget(self._x, 0, 1, 1, 2)
        g.addWidget(self._y, 1, 1, 1, 2)
        g.addWidget(QtWidgets.QPushButton("Copy", clicked=self._copy), 2, 1)
        g.addWidget(QtWidgets.QPushButton("Paste", clicked=self._paste), 2, 2)

        v = QtWidgets.QVBoxLayout()
        v.addLayout(g)
        v.addStretch()

        self.setLayout(v)

    @avoidCircularReference
    def _loadstate(self, *args, **kwargs):
        if len(self.data) != 0:
            x, y = self.data[0].getPosition()
            self._x.setValue(x)
            self._y.setValue(y)

    @avoidCircularReference
    def _chgPos(self, *args, **kwargs):
        if len(self.data) != 0:
            for d in self.data:
                d.setPosition([self._x.value(), self._y.value()])

    def _copy(self):
        if len(self.data) != 0:
            cb = QtWidgets.QApplication.clipboard()
            cb.clear(mode=cb.Clipboard)
            cb.setText(str(self.data[0].getPosition()), mode=cb.Clipboard)

    def _paste(self):
        cb = QtWidgets.QApplication.clipboard()
        v = np.array(eval(cb.text(mode=cb.Clipboard)))
        if v.shape[0] == 2:
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


class CrossAnnotationBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

        sel = AnnotationSelectionBox(canvas, 'cross')
        col = LineColorAdjustBox(canvas, 'cross')
        stl = LineStyleAdjustBox(canvas, 'cross')
        pos = _CrossPositionAdjustBox(canvas)
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
