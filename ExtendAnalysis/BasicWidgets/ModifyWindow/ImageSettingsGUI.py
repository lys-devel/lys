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
        self.__cmap.setOpacity(self.canvas.getOpacity(indexes)[0])
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
            self.canvas.setOpacity(indexes, self.__cmap.opacity())
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
        self.__rot.valueChanged.connect(self.__changerange)
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
            self.canvas.setColorRotation(indexes, self.__rot.value())


class VectorAdjustBox(QWidget):
    _pivots = ["tail", "middle", "tip"]

    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        canvas.dataSelected.connect(self.OnDataSelected)
        self.__initlayout()
        self.__flg = False

    def __initlayout(self):
        layout = QVBoxLayout()
        self.__pivot = QComboBox()
        self.__pivot.addItems(self._pivots)
        self.__pivot.currentTextChanged.connect(self.__changePivot)
        self.__scale = ScientificSpinBox()
        self.__scale.valueChanged.connect(self.__changeLength)
        self.__width = ScientificSpinBox()
        self.__width.valueChanged.connect(self.__changeWidth)
        self.__color = ColorSelection()
        self.__color.colorChanged.connect(self.__changeColor)
        self.__edgecolor = ColorSelection()
        self.__edgecolor.colorChanged.connect(self.__changeEdgeColor)

        grid1 = QGridLayout()
        grid1.addWidget(QLabel("face"), 0, 1)
        grid1.addWidget(QLabel("edge"), 0, 2)
        grid1.addWidget(self.__color, 1, 1)
        grid1.addWidget(self.__edgecolor, 1, 2)
        grp1 = QGroupBox("Color")
        grp1.setLayout(grid1)

        grid2 = QGridLayout()
        grid2.addWidget(QLabel("scale"), 0, 1)
        grid2.addWidget(QLabel("width"), 0, 2)
        grid2.addWidget(self.__scale, 1, 1)
        grid2.addWidget(self.__width, 1, 2)
        grp2 = QGroupBox("Size")
        grp2.setLayout(grid2)

        layout.addWidget(self.__pivot)
        layout.addWidget(grp1)
        layout.addWidget(grp2)
        layout.addStretch()
        self.setLayout(layout)

    def OnDataSelected(self):
        self.__flg = True
        indexes = self.canvas.getSelectedIndexes("vector")
        if len(indexes) == 0:
            return
        scale = self.canvas.getVectorScale(indexes)[0]
        if scale is None:
            self.__scale.setValue(0)
        else:
            self.__scale.setValue(scale)
        width = self.canvas.getVectorWidth(indexes)[0]
        if width is None:
            self.__width.setValue(0)
        else:
            self.__width.setValue(width)
        self.__flg = False
        col = self.canvas.getVectorColor(indexes, "face")[0]
        self.__color.setColor(col)
        col = self.canvas.getVectorColor(indexes, "edge")[0]
        self.__edgecolor.setColor(col)
        p = self.canvas.getVectorPivot(indexes)[0]
        self.__pivot.setCurrentIndex(self._pivots.index(p))

    def __changeLength(self, value):
        if not self.__flg:
            indexes = self.canvas.getSelectedIndexes("vector")
            self.canvas.setVectorScale(indexes, value)

    def __changeWidth(self, value):
        if not self.__flg:
            indexes = self.canvas.getSelectedIndexes("vector")
            self.canvas.setVectorWidth(indexes, value)

    def __changeColor(self, color):
        if not self.__flg:
            indexes = self.canvas.getSelectedIndexes("vector")
            self.canvas.setVectorColor(indexes, color, "face")

    def __changeEdgeColor(self, color):
        if not self.__flg:
            indexes = self.canvas.getSelectedIndexes("vector")
            self.canvas.setVectorColor(indexes, color, "edge")

    def __changePivot(self):
        if not self.__flg:
            indexes = self.canvas.getSelectedIndexes("vector")
            self.canvas.setVectorPivot(indexes, self.__pivot.currentText())


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
