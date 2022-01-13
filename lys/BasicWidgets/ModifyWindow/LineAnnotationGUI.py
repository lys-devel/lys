from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .ColorWidgets import *
from .AnnotationGUI import *


class AnnotColorAdjustBox(ColorSelection):
    def __init__(self, canvas, type="line"):
        super().__init__()
        self.type = type
        self.canvas = canvas
        self.colorChanged.connect(self.__changed)

    def OnClicked(self):
        indexes = self.canvas.getSelectedAnnotations(self.type)
        cols = self.canvas.getAnnotLineColor(indexes)
        if len(cols) == 0:
            return
        super().OnClicked()

    def __changed(self):
        indexes = self.canvas.getSelectedAnnotations(self.type)
        cols = self.canvas.getAnnotLineColor(indexes)
        if len(cols) == 0:
            return
        self.canvas.setAnnotLineColor(self.getColor(), indexes)

    def OnAnnotationSelected(self):
        indexes = self.canvas.getSelectedAnnotations(self.type)
        if len(indexes) == 0:
            return
        cols = self.canvas.getAnnotLineColor(indexes)
        self.setColor(cols[0])


class AnnotStyleAdjustBox(QGroupBox):
    __list = ['solid', 'dashed', 'dashdot', 'dotted', 'None']

    def __init__(self, canvas, type="line"):
        super().__init__("Line")
        self.type = type
        self.canvas = canvas

        layout = QGridLayout()
        self.__combo = QComboBox()
        self.__combo.addItems(AnnotStyleAdjustBox.__list)
        self.__combo.activated.connect(self.__changeStyle)
        self.__spin1 = QDoubleSpinBox()
        self.__spin1.valueChanged.connect(self.__valueChange)

        layout.addWidget(QLabel('Type'), 0, 0)
        layout.addWidget(self.__combo, 1, 0)
        layout.addWidget(QLabel('Width'), 0, 1)
        layout.addWidget(self.__spin1, 1, 1)

        self.setLayout(layout)

    def __changeStyle(self):
        indexes = self.canvas.getSelectedAnnotations(self.type)
        if len(indexes) == 0:
            return
        res = self.__combo.currentText()
        self.canvas.setAnnotLineStyle(res, indexes)

    def __valueChange(self):
        indexes = self.canvas.getSelectedAnnotations(self.type)
        if len(indexes) == 0:
            return
        self.canvas.setAnnotLineWidth(self.__spin1.value(), indexes)

    def OnAnnotationSelected(self):
        indexes = self.canvas.getSelectedAnnotations(self.type)
        if len(indexes) == 0:
            return
        cols = self.canvas.getAnnotLineStyle(indexes)
        res = cols[0]
        self.__combo.setCurrentIndex(AnnotStyleAdjustBox.__list.index(res))
        wids = self.canvas.getAnnotLineWidth(indexes)
        self.__spin1.setValue(wids[0])


class LineAnnotationBox(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        layout = QVBoxLayout()
        layout.addWidget(AnnotationSelectionBox(canvas, 'line'))
        tab = QTabWidget()
        lv1 = QVBoxLayout()
        lv1.addWidget(AnnotColorAdjustBox(canvas, 'line'))
        lv1.addWidget(AnnotStyleAdjustBox(canvas, 'line'))
        w = QWidget()
        w.setLayout(lv1)
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
