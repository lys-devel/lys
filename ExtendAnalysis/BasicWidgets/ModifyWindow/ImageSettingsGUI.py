import math
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .ColorWidgets import *

from ExtendAnalysis.BasicWidgets.Commons.ScientificSpinBox import *


class _rangeWidget(QGroupBox):
    valueChanged = pyqtSignal()

    def __init__(self, title, auto=50, mean=50, width=50):
        super().__init__(title)
        self.__mean = mean
        self.__wid = width
        self.__flg = False
        self.__autovalue = auto
        self.__initlayout()
        self.__setAuto()

    def __initlayout(self):
        layout = QVBoxLayout()
        l_h1 = QHBoxLayout()
        self.__auto = QPushButton("Auto")
        self.__auto.clicked.connect(self.__setAuto)
        self.__zero = QPushButton("Zero")
        self.__zero.clicked.connect(self.__setZero)
        self.__spin1 = QDoubleSpinBox()
        self.__spin1.setRange(0, 100)
        self.__spin2 = ScientificSpinBox()
        l_h1.addWidget(QLabel('Rel'))
        l_h1.addWidget(self.__spin1)
        l_h1.addWidget(QLabel('Abs'))
        l_h1.addWidget(self.__spin2)
        layout.addLayout(l_h1)
        self.__slider = QSlider(Qt.Horizontal)
        self.__slider.setRange(0, 100)
        l_h2 = QHBoxLayout()
        l_h2.addWidget(self.__slider)
        l_h2.addWidget(self.__auto)
        l_h2.addWidget(self.__zero)
        layout.addLayout(l_h2)
        self.__slider.valueChanged.connect(self.setSlider)
        self.__spin1.valueChanged.connect(self.setRelative)
        self.__spin2.valueChanged.connect(self.setAbsolute)
        self.setLayout(layout)

    def __setAuto(self):
        self.setRelative(self.__autovalue)

    def __setZero(self):
        self.setAbsolute(0)

    def setSlider(self, val):
        self.setRelative(val)

    def setRelative(self, val):
        if self.__flg:
            return
        self.__spin2.setValue(self.__mean + self.__wid * (val - 50) / 50)

    def setAbsolute(self, val):
        if self.__flg:
            return
        self.__flg = True
        self.__spin1.setValue((val - self.__mean) / self.__wid * 50 + 50)
        self.__spin2.setValue(val)
        self.__slider.setValue(int((val - self.__mean) / self.__wid * 50 + 50))
        self.__flg = False
        self.valueChanged.emit()

    def getValue(self):
        return self.__spin2.value()

    def setRange(self, mean, wid):
        self.__mean = mean
        self.__wid = wid
        if self.__wid == 0:
            self.__wid = 1

    def setLimit(self, min, max):
        self.__spin2.setRange(min, max)


class ImageColorAdjustBox(QWidget):

    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        canvas.dataSelected.connect(self.OnDataSelected)
        self.__initlayout()
        self.__flg = False

    def __initlayout(self):
        layout = QVBoxLayout()
        self.__cmap = ColormapSelection()
        self.__cmap.colorChanged.connect(self.__changeColormap)
        self.__start = _rangeWidget("First", 20)
        self.__end = _rangeWidget("Last", 80)
        self.__start.valueChanged.connect(self.__changerange)
        self.__end.valueChanged.connect(self.__changerange)
        layout.addWidget(self.__cmap)
        layout.addWidget(self.__start)
        layout.addWidget(self.__end)
        self.setLayout(layout)

    def OnDataSelected(self):
        self.__flg = True
        indexes = self.canvas.getSelectedIndexes(2)
        if len(indexes) == 0:
            return
        log = self.canvas.isLog(indexes)[0]
        self.__cmap.setLog(log)
        col = self.canvas.getColormap(indexes)[0]
        self.__cmap.setColormap(col)
        im = self.canvas.getDataFromIndexes(2, indexes)[0].wave.data
        self.__start.setRange(im.mean(), math.sqrt(im.var()) * 5)
        self.__end.setRange(im.mean(), math.sqrt(im.var()) * 5)
        ran = self.canvas.getColorRange(indexes)[0]
        self.__start.setAbsolute(ran[0])
        self.__end.setAbsolute(ran[1])
        self.__flg = False

    def __changerange(self):
        if not self.__flg:
            indexes = self.canvas.getSelectedIndexes(2)
            self.canvas.setColorRange(indexes, self.__start.getValue(), self.__end.getValue(), self.__cmap.isLog())

    def __changeColormap(self):
        if not self.__flg:
            indexes = self.canvas.getSelectedIndexes(2)
            self.canvas.setColormap(self.__cmap.currentColor(), indexes)
            self.__changerange()


class RGBColorAdjustBox(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        canvas.dataSelected.connect(self.OnDataSelected)
        self.__initlayout()
        self.__flg = False

    def __initlayout(self):
        layout = QVBoxLayout()
        self.__rot = ScientificSpinBox()
        self.__rot.valueChanged.connect(self.__changeRange)
        self.__start = _rangeWidget("First", 20)
        self.__end = _rangeWidget("Last", 80)
        self.__start.valueChanged.connect(self.__changerange)
        self.__end.valueChanged.connect(self.__changerange)
        layout.addWidget(self.__rot)
        layout.addWidget(self.__start)
        layout.addWidget(self.__end)
        self.setLayout(layout)

    def OnDataSelected(self):
        self.__flg = True
        indexes = self.canvas.getSelectedIndexes(3)
        if len(indexes) == 0:
            return
        im = abs(self.canvas.getDataFromIndexes(3, indexes)[0].wave.data)
        self.__start.setRange(im.mean(), math.sqrt(im.var()) * 5)
        self.__end.setRange(im.mean(), math.sqrt(im.var()) * 5)
        ran = self.canvas.getColorRange(indexes)[0]
        self.__start.setAbsolute(ran[0])
        self.__end.setAbsolute(ran[1])
        self.__flg = False

    def __changerange(self):
        if not self.__flg:
            indexes = self.canvas.getSelectedIndexes(3)
            self.canvas.setColorRange(indexes, self.__start.getValue(), self.__end.getValue())
            self.canvas.setColorRotation(indexes, self.__rot.getValue())


class ImagePlaneAdjustBox(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        canvas.dataSelected.connect(self.OnDataSelected)
        self.__initlayout()
        self.__flg = False
        self.index = None
        self.zaxis = None

    def __initlayout(self):
        layout = QVBoxLayout()
        l_h1 = QHBoxLayout()
        self.__spin1 = QSpinBox()
        self.__spin2 = QDoubleSpinBox()
        l_h1.addWidget(QLabel('z index'))
        l_h1.addWidget(self.__spin1)
        l_h1.addWidget(QLabel('z value'))
        l_h1.addWidget(self.__spin2)
        layout.addLayout(l_h1)
        self.__slider = QSlider(Qt.Horizontal)
        self.__slider.setRange(0, 100)
        layout.addWidget(self.__slider)
        self.__slider.valueChanged.connect(self.__spin1.setValue)
        self.__spin1.valueChanged.connect(self._setPlane)
        self.setLayout(layout)

    def OnDataSelected(self):
        self.__flg = True
        indexes = self.canvas.getSelectedIndexes(2)
        if not len(indexes) == 0:
            data = self.canvas.getDataFromIndexes(2, indexes)
            data_3d = []
            for d in data:
                if d.wave.data.ndim >= 3:
                    data_3d.append(d)
            if not len(data_3d) == 0:
                zaxis = data_3d[0].wave.z
                self.index = data_3d[0].id
                self.__spin1.setRange(0, len(zaxis) - 1)
                self.__slider.setRange(0, len(zaxis) - 1)
                self.zaxis = zaxis
                zindex = data_3d[0].zindex
                self.__spin1.setValue(zindex)
        self.__flg = False

    def _setPlane(self):
        indexes = self.canvas.getSelectedIndexes(2)
        zval = self.__spin1.value()
        self.__spin2.setValue(self.zaxis[zval])
        self.__slider.setValue(zval)
        if self.__flg:
            return
        if not len(indexes) == 0:
            self.canvas.setIndex(self.index, zval)


class AnimationBox(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.__initlayout()

    def __initlayout(self):
        layout = QVBoxLayout()
        l_h1 = QHBoxLayout()
        self.__start = QPushButton('Start')
        self.__start.clicked.connect(self.canvas.StartAnimation)
        self.__stop = QPushButton('Stop')
        self.__stop.clicked.connect(self.canvas.StopAnimation)
        l_h1.addWidget(self.__start)
        l_h1.addWidget(self.__stop)
        layout.addLayout(l_h1)
        self.setLayout(layout)
