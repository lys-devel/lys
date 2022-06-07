from lys.Qt import QtWidgets
from lys.widgets import ScientificSpinBox, ColormapSelection, ColorSelection


class _rangeWidget(QtWidgets.QHBoxLayout):
    def __init__(self, title, auto=0):
        super().__init__()
        self.__autovalue = auto
        self.__initlayout(title)
        self.valueChanged = self.__spin2.valueChanged

    def __initlayout(self, title):
        self.__spin2 = ScientificSpinBox()
        self.__spin2.valueChanged.connect(self.setAbsolute)

        self.addWidget(QtWidgets.QLabel(title))
        self.addWidget(self.__spin2)
        self.addWidget(QtWidgets.QPushButton("Auto", clicked=lambda: self.setAbsolute(self.__autovalue)))
        self.addWidget(QtWidgets.QPushButton("Zero", clicked=lambda: self.setAbsolute(0)))

    def setAbsolute(self, val):
        self.__spin2.setValue(val)

    def getValue(self):
        return self.__spin2.value()

    def setAutoValue(self, val):
        self.__autovalue = val


class ImageColorAdjustBox(QtWidgets.QWidget):
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

        layout = QtWidgets.QVBoxLayout()
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


class RGBColorAdjustBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.__loadflg = False
        self.__initlayout()

    def __initlayout(self):
        self.__rot = QtWidgets.QDoubleSpinBox()
        self.__rot.setRange(0, 360)
        self.__rot.valueChanged.connect(self.__changerot)
        self.__start = _rangeWidget("Min", 0)
        self.__end = _rangeWidget("Max", 1)
        self.__start.valueChanged.connect(self.__changerange)
        self.__end.valueChanged.connect(self.__changerange)

        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(QtWidgets.QLabel('Color Rotation'))
        h1.addWidget(self.__rot)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(h1)
        layout.addLayout(self.__start)
        layout.addLayout(self.__end)
        layout.addStretch()
        self.setLayout(layout)

    def setRGBs(self, images):
        self._images = images
        if len(images) != 0:
            self.__loadflg = True
            self.__rot.setValue(images[0].getColorRotation())
            min, max = images[0].getAutoColorRange()
            self.__start.setAutoValue(min)
            self.__end.setAutoValue(max)
            min, max = images[0].getColorRange()
            self.__start.setAbsolute(min)
            self.__end.setAbsolute(max)
            self.__loadflg = False

    def __changerange(self):
        if not self.__loadflg:
            for im in self._images:
                im.setColorRange(self.__start.getValue(), self.__end.getValue())

    def __changerot(self):
        if not self.__loadflg:
            for im in self._images:
                im.setColorRotation(self.__rot.value())


class VectorAdjustBox(QtWidgets.QWidget):
    _pivots = ["tail", "middle", "tip"]

    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.__initlayout()
        self.__flg = False

    def __initlayout(self):
        self.__pivot = QtWidgets.QComboBox()
        self.__pivot.addItems(self._pivots)
        self.__pivot.currentTextChanged.connect(self.__changePivot)
        self.__scale = ScientificSpinBox()
        self.__scale.valueChanged.connect(self.__changeLength)
        self.__width = ScientificSpinBox()
        self.__width.valueChanged.connect(self.__changeWidth)
        self.__color = ColorSelection()
        self.__color.colorChanged.connect(self.__changeColor)

        grid1 = QtWidgets.QGridLayout()
        grid1.addWidget(QtWidgets.QLabel("Pivot"), 0, 0)
        grid1.addWidget(QtWidgets.QLabel("color"), 1, 0)
        grid1.addWidget(QtWidgets.QLabel("scale"), 2, 0)
        grid1.addWidget(QtWidgets.QLabel("width"), 3, 0)
        grid1.addWidget(self.__pivot, 0, 1)
        grid1.addWidget(self.__color, 1, 1)
        grid1.addWidget(self.__scale, 2, 1)
        grid1.addWidget(self.__width, 3, 1)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(grid1)
        layout.addStretch()
        self.setLayout(layout)

    def setVectors(self, vectors):
        self._vectors = vectors
        self.__flg = True
        if len(vectors) != 0:
            self.__scale.setValue(vectors[0].getScale())
            self.__width.setValue(vectors[0].getWidth())
            self.__color.setColor(vectors[0].getColor())
            self.__pivot.setCurrentText(vectors[0].getPivot())
        self.__flg = False

    def __changeLength(self, value):
        if not self.__flg:
            for v in self._vectors:
                v.setScale(value)

    def __changeWidth(self, value):
        if not self.__flg:
            for v in self._vectors:
                v.setWidth(value)

    def __changeColor(self, color):
        if not self.__flg:
            for v in self._vectors:
                v.setColor(color)

    def __changePivot(self):
        if not self.__flg:
            for v in self._vectors:
                v.setPivot(self.__pivot.currentText())
