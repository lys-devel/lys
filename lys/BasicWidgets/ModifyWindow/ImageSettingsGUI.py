import math
from LysQt.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QWidget, QComboBox, QGroupBox, QGridLayout

from lys.widgets import ScientificSpinBox
from .ColorWidgets import ColormapSelection, ColorSelection


class _rangeWidget(QHBoxLayout):
    def __init__(self, title, auto=0):
        super().__init__()
        self.__autovalue = auto
        self.__initlayout(title)
        self.valueChanged = self.__spin2.valueChanged

    def __initlayout(self, title):
        self.__spin2 = ScientificSpinBox()
        self.__spin2.valueChanged.connect(self.setAbsolute)

        self.addWidget(QLabel(title))
        self.addWidget(self.__spin2)
        self.addWidget(QPushButton("Auto", clicked=lambda: self.setAbsolute(self.__autovalue)))
        self.addWidget(QPushButton("Zero", clicked=lambda: self.setAbsolute(0)))

    def setAbsolute(self, val):
        self.__spin2.setValue(val)

    def getValue(self):
        return self.__spin2.value()

    def setAutoValue(self, val):
        self.__autovalue = val


class ImageColorAdjustBox(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.__initlayout()
        self.__loadflg = False

    def __initlayout(self):
        self.__cmap = ColormapSelection()
        self.__cmap.colorChanged.connect(self.__changeColormap)
        self.__start = _rangeWidget("Min", 0)
        self.__end = _rangeWidget("Max", 1)
        self.__start.valueChanged.connect(self.__changerange)
        self.__end.valueChanged.connect(self.__changerange)

        layout = QVBoxLayout()
        layout.addWidget(self.__cmap)
        layout.addLayout(self.__start)
        layout.addLayout(self.__end)
        layout.addStretch()
        self.setLayout(layout)

    def __changerange(self):
        if self.__loadflg:
            return
        for im in self._images:
            im.setColorRange(self.__start.getValue(), self.__end.getValue())
            im.setLog(self.__cmap.isLog())

    def __changeColormap(self):
        if self.__loadflg:
            return
        for im in self._images:
            im.setColormap(self.__cmap.currentColor())
            im.setGamma(self.__cmap.gamma())
            im.setOpacity(self.__cmap.opacity())
        self.__changerange()

    def setImages(self, images):
        self._images = images
        if len(images) != 0:
            self.__loadflg = True
            self.__cmap.setColormap(images[0].getColormap())
            self.__cmap.setOpacity(images[0].getOpacity())
            self.__cmap.setGamma(images[0].getGamma())
            self.__cmap.setLog(images[0].isLog())
            min, max = images[0].getAutoColorRange()
            self.__start.setAutoValue(min)
            self.__end.setAutoValue(max)
            min, max = images[0].getColorRange()
            self.__start.setAbsolute(min)
            self.__end.setAbsolute(max)
            self.__loadflg = False


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
