import pyqtgraph
import numpy as np
from matplotlib.figure import Figure, SubplotParams
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import cm
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import collections
import matplotlib.cm

# Before import this file, be sure that QGuiApplication instance is initialized.


class ColorSelection(QPushButton):
    colorChanged = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.clicked.connect(self.OnClicked)
        self.__color = "black"

    def OnClicked(self):
        res = QColorDialog.getColor(QColor(self.getColor()))
        if res.isValid():
            c = (res.red() / 255.0, res.green() / 255.0, res.blue() / 255.0, res.alpha() / 255.0)
            self.setColor(res.name())
            self.colorChanged.emit(c)

    def setColor(self, color):
        if isinstance(color, tuple) or isinstance(color, list):
            if len(color) == 4:
                self.__color = "rgba" + str((int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), int(color[3])))
            if len(color) == 3:
                self.__color = "rgba" + str((color[0] * 255, color[1] * 255, color[2] * 255, 1))
        else:
            self.__color = color
        self.setStyleSheet("background-color:" + self.__color)

    def getColor(self):
        return self.__color

    def getColorAsArray(self):
        return QColor(self.getColor())


cmaps = [('Perceptually Uniform Sequential', [
    'viridis', 'plasma', 'inferno', 'magma']),
    ('Sequential', [
        'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
        'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
        'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']),
    ('Sequential (2)', [
        'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink',
        'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia',
        'hot', 'afmhot', 'gist_heat', 'copper']),
    ('Diverging', [
        'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu',
        'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic']),
    ('Qualitative', [
        'Pastel1', 'Pastel2', 'Paired', 'Accent',
        'Dark2', 'Set1', 'Set2', 'Set3']),
    ('Miscellaneous', [
        'flag', 'prism', 'ocean', 'gist_earth', 'terrain', 'gist_stern',
        'gnuplot', 'gnuplot2', 'CMRmap', 'cubehelix', 'brg', 'hsv',
        'gist_rainbow', 'rainbow', 'jet', 'nipy_spectral', 'gist_ncar'])]
cmapdic = {}


def cmap2pixmap(cmap, steps=128):
    sm = cm.ScalarMappable(cmap=cmap)
    sm.norm.vmin = 0.0
    sm.norm.vmax = 1.0
    inds = np.linspace(0, 1, steps)
    rgbas = sm.to_rgba(inds)
    rgbas = [QColor(int(r * 255), int(g * 255),
                    int(b * 255), int(a * 255)).rgba() for r, g, b, a in rgbas]
    im = QImage(steps, 1, QImage.Format_Indexed8)
    im.setColorTable(rgbas)
    for i in range(steps):
        im.setPixel(i, 0, i)
    im = im.scaled(100, 15)
    pm = QPixmap.fromImage(im)
    return pm


def loadCmaps():
    for item in cmaps:
        for i in item[1]:
            cmapdic[i] = cmap2pixmap(i)


loadCmaps()


class ColormapSelection(QWidget):
    colorChanged = pyqtSignal()

    class ColorCombo(QComboBox):
        def __init__(self):
            super().__init__()
            model = QStandardItemModel()
            self.setModel(model)
            self.__list = []
            n = 0
            for item in cmaps:
                for i in item[1]:
                    data = QStandardItem(i)
                    data.setData(cmapdic[i], Qt.DecorationRole)
                    model.setItem(n, data)
                    self.__list.append(i)
                    n += 1

        def setColormap(self, cmap):
            self.setCurrentIndex(self.__list.index(cmap))

    def __init__(self):
        super().__init__()
        self.__combo = ColormapSelection.ColorCombo()
        self.__combo.activated.connect(self.__changed)
        self.__opacity = QDoubleSpinBox()
        self.__opacity.setRange(0, 1)
        self.__opacity.setSingleStep(0.1)
        self.__opacity.setDecimals(2)
        self.__opacity.valueChanged.connect(self.__changed)
        self.__check = QCheckBox("Reverse")
        self.__check.stateChanged.connect(self.__changed)
        self.__log = QCheckBox("Log")
        self.__log.stateChanged.connect(self.__changed)
        layout = QVBoxLayout()

        layout_h = QHBoxLayout()
        layout_h.addWidget(QLabel('Opacity'))
        layout_h.addWidget(self.__opacity)
        layout_h.addWidget(self.__check)
        layout_h.addWidget(self.__log)

        layout.addLayout(layout_h)
        layout.addWidget(self.__combo)
        self.setLayout(layout)

    def __changed(self):
        self.colorChanged.emit()

    def setColormap(self, cmap):
        tmp = cmap.split('_')
        self.__combo.setColormap(tmp[0])
        self.__check.setChecked(not len(tmp) == 1)

    def currentColor(self):
        if self.__check.isChecked():
            return self.__combo.currentText() + "_r"
        else:
            return self.__combo.currentText()

    def currentColorMaps(self):
        return cmapdic[self.currentColor()]

    def isLog(self):
        return self.__log.isChecked()

    def setLog(self, value):
        self.__log.setChecked(value)

    def setOpacity(self, value):
        self.__opacity.setValue(value)

    def opacity(self):
        return self.__opacity.value()


def cmapToColormap(cmap, nTicks=16):
    """
    Converts a Matplotlib cmap to pyqtgraphs colormaps. No dependency on matplotlib.
    Parameters:
    *cmap*: Cmap object. Imported from matplotlib.cm.*
    *nTicks*: Number of ticks to create when dict of functions is used. Otherwise unused.
    """

    # Case #1: a dictionary with 'red'/'green'/'blue' values as list of ranges (e.g. 'jet')
    # The parameter 'cmap' is a 'matplotlib.colors.LinearSegmentedColormap' instance ...
    if hasattr(cmap, '_segmentdata'):
        colordata = getattr(cmap, '_segmentdata')
        if ('red' in colordata) and isinstance(colordata['red'], collections.Sequence):
            # print("[cmapToColormap] RGB dicts with ranges")

            # collect the color ranges from all channels into one dict to get unique indices
            posDict = {}
            for idx, channel in enumerate(('red', 'green', 'blue')):
                for colorRange in colordata[channel]:
                    posDict.setdefault(colorRange[0], [-1, -1, -1])[idx] = colorRange[2]

            indexList = list(posDict.keys())
            indexList.sort()
            # interpolate missing values (== -1)
            for channel in range(3):  # R,G,B
                startIdx = indexList[0]
                emptyIdx = []
                for curIdx in indexList:
                    if posDict[curIdx][channel] == -1:
                        emptyIdx.append(curIdx)
                    elif curIdx != indexList[0]:
                        for eIdx in emptyIdx:
                            rPos = (eIdx - startIdx) / (curIdx - startIdx)
                            vStart = posDict[startIdx][channel]
                            vRange = (posDict[curIdx][channel] - posDict[startIdx][channel])
                            posDict[eIdx][channel] = rPos * vRange + vStart
                        startIdx = curIdx
                        del emptyIdx[:]
            for channel in range(3):  # R,G,B
                for curIdx in indexList:
                    posDict[curIdx][channel] *= 255

            posList = [[i, posDict[i]] for i in indexList]
            return posList

        # Case #2: a dictionary with 'red'/'green'/'blue' values as functions (e.g. 'gnuplot')
        elif ('red' in colordata) and isinstance(colordata['red'], collections.Callable):
            # print("[cmapToColormap] RGB dict with functions")
            indices = np.linspace(0., 1., nTicks)
            luts = [np.clip(np.array(colordata[rgb](indices), dtype=np.float), 0, 1) * 255
                    for rgb in ('red', 'green', 'blue')]
            return list(zip(indices, list(zip(*luts))))

    # If the parameter 'cmap' is a 'matplotlib.colors.ListedColormap' instance, with the attributes 'colors' and 'N'
    elif hasattr(cmap, 'colors') and hasattr(cmap, 'N'):
        colordata = getattr(cmap, 'colors')
        # Case #3: a list with RGB values (e.g. 'seismic')
        if len(colordata[0]) == 3:
            # print("[cmapToColormap] list with RGB values")
            indices = np.linspace(0., 1., len(colordata))
            scaledRgbTuples = [(rgbTuple[0] * 255, rgbTuple[1] * 255, rgbTuple[2] * 255) for rgbTuple in colordata]
            return list(zip(indices, scaledRgbTuples))

        # Case #4: a list of tuples with positions and RGB-values (e.g. 'terrain')
        # -> this section is probably not needed anymore!?
        elif len(colordata[0]) == 2:
            # print("[cmapToColormap] list with positions and RGB-values. Just scale the values.")
            scaledCmap = [(idx, (vals[0] * 255, vals[1] * 255, vals[2] * 255)) for idx, vals in colordata]
            return scaledCmap

    # Case #X: unknown format or datatype was the wrong object type
    else:
        raise ValueError("[cmapToColormap] Unknown cmap format or not a cmap!")
