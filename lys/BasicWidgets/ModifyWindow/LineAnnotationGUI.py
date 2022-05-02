import numpy as np
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QComboBox, QDoubleSpinBox, QLabel, QWidget, QVBoxLayout, QTabWidget, QPushButton, QApplication

from lys.widgets import ColorSelection, ScientificSpinBox
from lys.decorators import avoidCircularReference

from .AnnotationGUI import AnnotationSelectionBox


class _LineColorAdjustBox(ColorSelection):
    def __init__(self, canvas, type="line"):
        super().__init__()
        self.type = type
        self.canvas = canvas
        self.colorChanged.connect(self.__changed)

    def __changed(self):
        for d in self.data:
            d.setLineColor(self.getColor())

    def _loadstate(self):
        if len(self.data) != 0:
            self.setColor(self.data[0].getLineColor())

    def setData(self, data):
        self.data = data
        self._loadstate()


class _LineStyleAdjustBox(QGroupBox):
    __list = ['solid', 'dashed', 'dashdot', 'dotted', 'None']

    def __init__(self, canvas, type="line"):
        super().__init__("Line")
        self.type = type
        self.canvas = canvas

        self.__combo = QComboBox()
        self.__combo.addItems(self.__list)
        self.__combo.activated.connect(self.__changeStyle)
        self.__spin1 = QDoubleSpinBox()
        self.__spin1.valueChanged.connect(self.__valueChange)

        layout = QGridLayout()
        layout.addWidget(QLabel('Type'), 0, 0)
        layout.addWidget(self.__combo, 1, 0)
        layout.addWidget(QLabel('Width'), 0, 1)
        layout.addWidget(self.__spin1, 1, 1)

        self.setLayout(layout)

    def __changeStyle(self):
        res = self.__combo.currentText()
        for d in self.data:
            d.setLineStyle(res)

    def __valueChange(self):
        val = self.__spin1.value()
        for d in self.data:
            d.setLineWidth(val)

    def _loadstate(self):
        if len(self.data) != 0:
            d = self.data[0]
            self.__combo.setCurrentText(d.getLineStyle())
            self.__spin1.setValue(d.getLineWidth())

    def setData(self, data):
        self.data = data
        self._loadstate()


class _LinePositionAdjustBox(QWidget):
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
            cb = QApplication.clipboard()
            cb.clear(mode=cb.Clipboard)
            cb.setText(str(self.data[0].getPosition()), mode=cb.Clipboard)

    def _paste(self):
        cb = QApplication.clipboard()
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


class LineAnnotationBox(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

        sel = AnnotationSelectionBox(canvas, 'line')
        col = _LineColorAdjustBox(canvas, 'line')
        stl = _LineStyleAdjustBox(canvas, 'line')
        pos = _LinePositionAdjustBox(canvas)
        sel.selected.connect(col.setData)
        sel.selected.connect(stl.setData)
        sel.selected.connect(pos.setData)

        layout = QVBoxLayout()
        layout.addWidget(sel)

        lv1 = QVBoxLayout()
        lv1.addWidget(QLabel('Color'))
        lv1.addWidget(col)
        lv1.addWidget(stl)
        w = QWidget()
        w.setLayout(lv1)

        tab = QTabWidget()
        tab.addTab(pos, 'Position')
        tab.addTab(w, 'Appearance')
        layout.addWidget(tab)
        self.setLayout(layout)


class RectAnnotationBox(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        layout = QVBoxLayout()
        layout.addWidget(AnnotationSelectionBox(canvas, 'rect'))
        tab = QTabWidget()
        lv1 = QVBoxLayout()
        lv1.addWidget(AnnotColorAdjustBox(canvas, 'rect'))
        lv1.addWidget(AnnotStyleAdjustBox(canvas, 'rect'))
        w = QWidget()
        w.setLayout(lv1)
        tab.addTab(w, 'Appearance')
        layout.addWidget(tab)
        self.setLayout(layout)
