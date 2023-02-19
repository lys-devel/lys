import numpy as np
from matplotlib import cm

from lys.Qt import QtWidgets
from lys.widgets import ScientificSpinBox, ColormapSelection, ColorSelection
from lys.decorators import avoidCircularReference

from .LineSettingsGUI import _LineStyleAdjustBox, _LineColorSideBySideDialog


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
        self.__auto = QtWidgets.QPushButton("Auto", clicked=lambda: self.setAbsolute(self.__autovalue))
        self.__zero = QtWidgets.QPushButton("Zero", clicked=lambda: self.setAbsolute(0))
        self.addWidget(self.__auto)
        self.addWidget(self.__zero)

    def setAbsolute(self, val):
        self.__spin2.setValue(val)

    def getValue(self):
        return self.__spin2.value()

    def setAutoValue(self, val):
        self.__autovalue = val

    def setEnabled(self, b):
        self.__spin2.setEnabled(b)
        self.__auto.setEnabled(b)
        self.__zero.setEnabled(b)


class ImageColorAdjustBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.__initlayout()
        self.__setEnabled(False)

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

    def __setEnabled(self, b):
        self.__cmap.setEnabled(b)
        self.__start.setEnabled(b)
        self.__end.setEnabled(b)

    @avoidCircularReference
    def __changerange(self, *args, **kwargs):
        for im in self._images:
            im.setColorRange(self.__start.getValue(), self.__end.getValue())
            im.setLog(self.__cmap.isLog())

    @avoidCircularReference
    def __changeColormap(self, *args, **kwargs):
        for im in self._images:
            im.setColormap(self.__cmap.currentColor())
            im.setGamma(self.__cmap.gamma())
            im.setOpacity(self.__cmap.opacity())
        self.__changerange()

    @avoidCircularReference
    def setImages(self, images):
        self._images = images
        if len(images) != 0:
            self.__setEnabled(True)
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
        else:
            self.__setEnabled(False)


class ColorbarAdjustBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.__initlayout()
        self.__setEnabled(False)

    def __initlayout(self):
        self.__vis = QtWidgets.QCheckBox("Show colorbar")
        self.__vis.toggled.connect(self.__enabled)

        self.__dir = QtWidgets.QComboBox()
        self.__dir.addItems(["vertical", "horizontal"])
        self.__dir.currentTextChanged.connect(self.__setDirection)

        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(self.__vis)
        h1.addWidget(self.__dir)

        self.__x = QtWidgets.QDoubleSpinBox()
        self.__x.setSingleStep(0.01)
        self.__x.setRange(-1, 2)
        self.__x.valueChanged.connect(self.__setColorbarSize)
        self.__y = QtWidgets.QDoubleSpinBox()
        self.__y.setSingleStep(0.1)
        self.__y.setRange(-1, 2)
        self.__y.valueChanged.connect(self.__setColorbarSize)
        self.__wid = QtWidgets.QDoubleSpinBox()
        self.__wid.setSingleStep(0.01)
        self.__wid.setRange(0, 2)
        self.__wid.valueChanged.connect(self.__setColorbarSize)
        self.__len = QtWidgets.QDoubleSpinBox()
        self.__len.setSingleStep(0.1)
        self.__len.setRange(0, 2)
        self.__len.valueChanged.connect(self.__setColorbarSize)

        g1 = QtWidgets.QGridLayout()
        g1.addWidget(QtWidgets.QLabel("x"), 0, 0)
        g1.addWidget(QtWidgets.QLabel("y"), 0, 1)
        g1.addWidget(self.__x, 1, 0)
        g1.addWidget(self.__y, 1, 1)
        g1.addWidget(QtWidgets.QLabel("Width"), 2, 0)
        g1.addWidget(QtWidgets.QLabel("Length"), 2, 1)
        g1.addWidget(self.__wid, 3, 0)
        g1.addWidget(self.__len, 3, 1)
        grp1 = QtWidgets.QGroupBox("Position and size")
        grp1.setLayout(g1)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(h1)
        layout.addWidget(grp1)
        layout.addStretch()
        self.setLayout(layout)

    def __setEnabled(self, b):
        self.__vis.setEnabled(b)
        self.__len.setEnabled(b)
        self.__wid.setEnabled(b)
        self.__x.setEnabled(b)
        self.__y.setEnabled(b)

    def __enabled(self, b):
        for im in self._images:
            im.setColorbarVisible(b)
        self.__x.setEnabled(b)
        self.__y.setEnabled(b)
        self.__len.setEnabled(b)
        self.__wid.setEnabled(b)

    @ avoidCircularReference
    def __setColorbarSize(self, *args):
        for im in self._images:
            im.setColorbarPosition((self.__x.value(), self.__y.value()))
            im.setColorbarSize((self.__wid.value(), self.__len.value()))

    @ avoidCircularReference
    def __setDirection(self, dir):
        for im in self._images:
            im.setColorbarDirection(dir)

    @ avoidCircularReference
    def setData(self, images):
        self._images = images
        if len(images) != 0:
            self.__setEnabled(True)
            self.__vis.setChecked(images[0].getColorbarVisible())
            self.__enabled(images[0].getColorbarVisible())
            self.__x.setValue(images[0].getColorbarPosition()[0])
            self.__y.setValue(images[0].getColorbarPosition()[1])
            self.__wid.setValue(images[0].getColorbarSize()[0])
            self.__len.setValue(images[0].getColorbarSize()[1])
        else:
            self.__setEnabled(False)


class RGBColorAdjustBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.__initlayout()
        self.__setEnable(False)

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

    @ avoidCircularReference
    def setRGBs(self, images):
        self._images = images
        if len(images) != 0:
            self.__setEnable(True)
            self.__rot.setEnabled(np.array([len(i.getFilteredWave().shape) == 2 for i in images]).any())
            self.__rot.setValue(images[0].getColorRotation())
            min, max = images[0].getAutoColorRange()
            self.__start.setAutoValue(min)
            self.__end.setAutoValue(max)
            min, max = images[0].getColorRange()
            self.__start.setAbsolute(min)
            self.__end.setAbsolute(max)
        else:
            self.__setEnable(False)

    def __setEnable(self, b):
        self.__rot.setEnabled(b)
        self.__start.setEnabled(b)
        self.__end.setEnabled(b)

    @ avoidCircularReference
    def __changerange(self, *args, **kwargs):
        for im in self._images:
            im.setColorRange(self.__start.getValue(), self.__end.getValue())

    @ avoidCircularReference
    def __changerot(self, *args, **kwargs):
        for im in self._images:
            im.setColorRotation(self.__rot.value())


class RGBMapAdjustBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self._canvas = canvas
        self.__initlayout()

    def __initlayout(self):
        self.__check = QtWidgets.QCheckBox("Show colormap", toggled=self.__visible)
        self.__pos1 = QtWidgets.QDoubleSpinBox(valueChanged=self.__changePos)
        self.__pos1.setRange(-2, 2)
        self.__pos1.setSingleStep(0.05)
        self.__pos2 = QtWidgets.QDoubleSpinBox(valueChanged=self.__changePos)
        self.__pos2.setRange(-2, 2)
        self.__pos2.setSingleStep(0.05)
        self.__size = QtWidgets.QDoubleSpinBox(valueChanged=self.__changeSize)
        self.__size.setRange(0, 2)
        self.__size.setSingleStep(0.05)

        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("x"), 0, 0)
        grid.addWidget(QtWidgets.QLabel("y"), 0, 1)
        grid.addWidget(QtWidgets.QLabel("size"), 0, 2)
        grid.addWidget(self.__pos1, 1, 0)
        grid.addWidget(self.__pos2, 1, 1)
        grid.addWidget(self.__size, 1, 2)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.__check)
        layout.addLayout(grid)
        layout.addStretch()
        self.setLayout(layout)

    def __setEnable(self, b):
        self.__check.setEnabled(b)
        if b:
            self.__pos1.setEnabled(self.__check.isChecked())
            self.__pos2.setEnabled(self.__check.isChecked())
            self.__size.setEnabled(self.__check.isChecked())
        else:
            self.__pos1.setEnabled(b)
            self.__pos2.setEnabled(b)
            self.__size.setEnabled(b)

    @ avoidCircularReference
    def setRGBs(self, images):
        self._images = images
        if len(images) != 0:
            self.__check.setChecked(images[0].getColormapVisible())
            pos = images[0].getColormapPosition()
            self.__pos1.setValue(pos[0])
            self.__pos2.setValue(pos[1])
            size = images[0].getColormapSize()
            self.__size.setValue(size)
            self.__setEnable(True)
        else:
            self.__setEnable(False)

    @ avoidCircularReference
    def __visible(self, *args, **kwargs):
        for im in self._images:
            im.setColormapVisible(self.__check.isChecked())
        self.__pos1.setEnabled(self.__check.isChecked())
        self.__pos2.setEnabled(self.__check.isChecked())
        self.__size.setEnabled(self.__check.isChecked())

    @ avoidCircularReference
    def __changePos(self, *args, **kwargs):
        for im in self._images:
            im.setColormapPosition([self.__pos1.value(), self.__pos2.value()])

    @ avoidCircularReference
    def __changeSize(self, *args, **kwargs):
        for im in self._images:
            im.setColormapSize(self.__size.value())


class VectorAdjustBox(QtWidgets.QWidget):
    _pivots = ["tail", "middle", "tip"]

    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.__initlayout()
        self.__setEnabled(False)

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

    def __setEnabled(self, b):
        self.__pivot.setEnabled(b)
        self.__scale.setEnabled(b)
        self.__width.setEnabled(b)
        self.__color.setEnabled(b)

    @ avoidCircularReference
    def setVectors(self, vectors):
        self._vectors = vectors
        if len(vectors) != 0:
            self.__setEnabled(True)
            self.__scale.setValue(vectors[0].getScale())
            self.__width.setValue(vectors[0].getWidth())
            self.__color.setColor(vectors[0].getColor())
            self.__pivot.setCurrentText(vectors[0].getPivot())
        else:
            self.__setEnabled(False)

    @ avoidCircularReference
    def __changeLength(self, value):
        for v in self._vectors:
            v.setScale(value)

    @ avoidCircularReference
    def __changeWidth(self, value):
        for v in self._vectors:
            v.setWidth(value)

    @ avoidCircularReference
    def __changeColor(self, color):
        for v in self._vectors:
            v.setColor(color)

    @ avoidCircularReference
    def __changePivot(self):
        for v in self._vectors:
            v.setPivot(self.__pivot.currentText())


class ContourAdjustBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.__initlayout(canvas)
        self.__setEnabled(False)

    def __initlayout(self, canvas):
        self.__level = ScientificSpinBox(valueChanged=self.__changeLevel)

        h2 = QtWidgets.QHBoxLayout()
        h2.addWidget(QtWidgets.QLabel("Level"))
        h2.addWidget(self.__level)
        h2.addWidget(QtWidgets.QPushButton("Side by side", clicked=self.__sideBySide_level))

        self.__color = ColorSelection()
        self.__color.colorChanged.connect(self.__changeColor)

        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(QtWidgets.QLabel("Color"))
        h1.addWidget(self.__color)
        h1.addWidget(QtWidgets.QPushButton("Side by side", clicked=self.__sideBySide_color))

        self._style = _LineStyleAdjustBox(canvas)
        self._style.widthChanged.connect(lambda w: [line.setWidth(w) for line in self._contours])
        self._style.styleChanged.connect(lambda s: [line.setStyle(s) for line in self._contours])

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(h2)
        layout.addLayout(h1)
        layout.addWidget(self._style)
        layout.addStretch()
        self.setLayout(layout)

    def __setEnabled(self, b):
        self.__color.setEnabled(b)
        self._style.setEnabled(b)

    @ avoidCircularReference
    def __changeColor(self, color):
        for c in self._contours:
            c.setColor(color)

    @ avoidCircularReference
    def __changeLevel(self, level):
        for c in self._contours:
            c.setLevel(level)

    @ avoidCircularReference
    def setContours(self, contours):
        self._contours = contours
        if len(contours) != 0:
            self.__setEnabled(True)
            self.__level.setValue(contours[0].getLevel())
            self.__color.setColor(contours[0].getColor())
            self._style.setWidth(contours[0].getWidth())
            self._style.setStyle(contours[0].getStyle())
        else:
            self.__setEnabled(False)

    def __sideBySide_color(self):
        d = _LineColorSideBySideDialog()
        res = d.exec_()
        if res == QtWidgets.QDialog.Accepted:
            c = d.getColor()
            if c == "" or c == "_r":
                return
            sm = cm.ScalarMappable(cmap=c)
            rgbas = sm.to_rgba(np.linspace(0, 1, len(self._contours)), bytes=True)
            rgbas = [('#{0:02x}{1:02x}{2:02x}').format(r, g, b) for r, g, b, a in rgbas]
            for line, color in zip(self._contours, rgbas):
                line.setColor(color)

    def __sideBySide_level(self):
        d = _LevelDialog(np.min([item.getLevel() for item in self._contours]))
        if d.exec_():
            fr, step = d.getParams()
            for i, item in enumerate(self._contours):
                item.setLevel(fr + step * i)


class _LevelDialog(QtWidgets.QDialog):
    def __init__(self, init, parent=None):
        super().__init__(parent)
        self._from = ScientificSpinBox()
        self._from.setValue(init)
        self._delta = ScientificSpinBox()
        self._delta.setValue(1)

        g = QtWidgets.QGridLayout()
        g.addWidget(QtWidgets.QLabel("From"), 0, 0)
        g.addWidget(self._from, 1, 0)
        g.addWidget(QtWidgets.QLabel("Delta"), 0, 1)
        g.addWidget(self._delta, 1, 1)

        g.addWidget(QtWidgets.QPushButton("O K", clicked=self.accept), 2, 0)
        g.addWidget(QtWidgets.QPushButton("CANCEL", clicked=self.reject), 2, 1)

        self.setLayout(g)

    def getParams(self):
        return self._from.value(), self._delta.value()
