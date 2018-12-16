from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .FontGUI import *

class AxisLabelAdjustBox(QGroupBox):
    def __init__(self,canvas):
        super().__init__("Axis Label")
        self.__flg=False
        self.canvas=canvas
        self.__initlayout()
        self.__loadstate()
        self.canvas.addAxisSelectedListener(self)
    def __getAxes(self):
        if self.__all.isChecked():
            return ['Left','Right','Bottom','Top']
        else:
            return [self.canvas.getSelectedAxis()]
    def __initlayout(self):
        l=QVBoxLayout()
        lay=QHBoxLayout()
        self.__all=QCheckBox('All axes')
        lay.addWidget(self.__all)
        self.__on=QCheckBox('Put label')
        self.__on.stateChanged.connect(self.__visible)
        lay.addWidget(self.__on)
        lay.addWidget(QLabel('Position'))
        self.__pos=QDoubleSpinBox()
        self.__pos.setRange(-1000,1000)
        self.__pos.setSingleStep(0.02)
        self.__pos.valueChanged.connect(self.__posChanged)
        lay.addWidget(self.__pos)
        l.addLayout(lay)
        self.__label=QTextEdit()
        self.__label.setMinimumHeight(10)
        self.__label.setMaximumHeight(50)
        self.__label.textChanged.connect(self.__labelChanged)
        l.addWidget(self.__label)
        self.setLayout(l)
    def __loadstate(self):
        self.__flg=True
        axis=self.canvas.getSelectedAxis()
        self.__on.setChecked(self.canvas.getAxisLabelVisible(axis))
        self.__label.setPlainText(self.canvas.getAxisLabel(axis))
        self.__pos.setValue(self.canvas.getAxisLabelCoords(axis))
        self.__flg=False
    def OnAxisSelected(self,axis):
        self.__loadstate()
    def __labelChanged(self):
        if self.__flg:
            return
        axis=self.canvas.getSelectedAxis()
        self.canvas.setAxisLabel(axis,self.__label.toPlainText())
    def __visible(self):
        if self.__flg:
            return
        for axis in self.__getAxes():
            self.canvas.setAxisLabelVisible(axis,self.__on.isChecked())
    def __posChanged(self):
        if self.__flg:
            return
        for axis in self.__getAxes():
            self.canvas.setAxisLabelCoords(axis,self.__pos.value())
class TickLabelAdjustBox(QGroupBox):
    def __init__(self,canvas):
        super().__init__("Tick Label")
        self.__flg=False
        self.canvas=canvas
        self.__initlayout()
        self.__loadstate()
        self.canvas.addAxisSelectedListener(self)
    def __getAxes(self):
        if self.__all.isChecked():
            return ['Left','Right','Bottom','Top']
        else:
            return [self.canvas.getSelectedAxis()]
    def __initlayout(self):
        l=QVBoxLayout()
        lay=QHBoxLayout()
        self.__all=QCheckBox('All axes')
        lay.addWidget(self.__all)
        self.__on=QCheckBox('Put label')
        self.__on.stateChanged.connect(self.__visible)
        lay.addWidget(self.__on)
        l.addLayout(lay)
        self.setLayout(l)
    def __loadstate(self):
        self.__flg=True
        axis=self.canvas.getSelectedAxis()
        self.__on.setChecked(self.canvas.getTickLabelVisible(axis))
        self.__flg=False
    def OnAxisSelected(self,axis):
        self.__loadstate()
    def __visible(self):
        if self.__flg:
            return
        for axis in self.__getAxes():
            self.canvas.setTickLabelVisible(axis,self.__on.isChecked())
class AxisAndTickLabelBox(QWidget):
    def __init__(self,canvas):
        super().__init__()
        layout=QVBoxLayout(self)
        layout.addWidget(FontSelectBox(canvas))
        layout.addWidget(AxisLabelAdjustBox(canvas))
        layout.addWidget(TickLabelAdjustBox(canvas))
        self.setLayout(layout)
class AxisFontBox(QWidget):
    def __init__(self,canvas):
        super().__init__()
        layout=QVBoxLayout(self)
        layout.addWidget(FontSelectBox(canvas))
        layout.addWidget(FontSelectBox(canvas,'Axis'))
        layout.addWidget(FontSelectBox(canvas,'Tick'))
        self.setLayout(layout)
