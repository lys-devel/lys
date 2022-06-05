
import math
import numpy as np
from matplotlib import cm
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor, QImage, QPixmap, QStandardItem, QStandardItemModel, QValidator
from PyQt5.QtWidgets import QPushButton, QColorDialog, QWidget, QDoubleSpinBox, QComboBox, QCheckBox, QVBoxLayout, QHBoxLayout, QLabel


class ScientificSpinBox(QDoubleSpinBox):
    """
    Spin box that displays values in sdientific notation, which is frequently used in lys.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setRange(-np.inf, np.inf)
        self.setDecimals(128)
        self.setAccelerated(True)

    def textFromValue(self, value):
        """textFromValue"""
        return "{:.6g}".format(value)

    def valueFromText(self, text):
        """Reimplementation of valueFromText"""
        return float(text)

    def validate(self, text, pos):
        """Reimplementation of validate"""
        try:
            float(text)
        except Exception:
            return (QValidator.Intermediate, text, pos)
        else:
            return (QValidator.Acceptable, text, pos)

    def stepBy(self, steps):
        """stepBy"""
        v = self.value()
        if v == 0:
            n = 1
        else:
            val = np.log10(abs(v))
            p = math.floor(val)
            if math.floor(abs(v) / (10**p)) == 1:  # and np.sign(steps) != np.sign(v):
                p = p - 1
            n = 10 ** p
        self.setValue(v + steps * n)


class ColorSelection(QPushButton):
    colorChanged = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.clicked.connect(self.OnClicked)
        self.__color = "black"

    def OnClicked(self):
        res = QColorDialog.getColor(QColor(self.getColor()))
        if res.isValid():
            self.setColor(res.name())
            self.colorChanged.emit(self.getColor())

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


_cmaps = [('Perceptually Uniform Sequential', [
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
_cmapdic = {}


def _cmap2pixmap(cmap, steps=128):
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


def _loadCmaps():
    for item in _cmaps:
        for i in item[1]:
            _cmapdic[i] = _cmap2pixmap(i)


_loadCmaps()


class ColormapSelection(QWidget):
    colorChanged = pyqtSignal()

    class _ColorCombo(QComboBox):
        def __init__(self):
            super().__init__()
            model = QStandardItemModel()
            self.setModel(model)
            self.__list = []
            n = 0
            for item in _cmaps:
                for i in item[1]:
                    data = QStandardItem(i)
                    data.setData(_cmapdic[i], Qt.DecorationRole)
                    model.setItem(n, data)
                    self.__list.append(i)
                    n += 1

        def setColormap(self, cmap):
            self.setCurrentIndex(self.__list.index(cmap))

    def __init__(self, opacity=True, log=True, reverse=True, gamma=True):
        super().__init__()
        self.__combo = ColormapSelection._ColorCombo()
        self.__combo.activated.connect(self.__changed)
        self.__opacity = QDoubleSpinBox()
        self.__opacity.setRange(0, 1)
        self.__opacity.setSingleStep(0.1)
        self.__opacity.setDecimals(2)
        self.__opacity.valueChanged.connect(self.__changed)
        self.__gamma = ScientificSpinBox()
        self.__gamma.setRange(0, 1000)
        self.__gamma.setDecimals(2)
        self.__gamma.valueChanged.connect(self.__changed)
        self.__check = QCheckBox("Rev")
        self.__check.stateChanged.connect(self.__changed)
        self.__log = QCheckBox("Log")
        self.__log.stateChanged.connect(self.__changed)
        layout = QVBoxLayout()

        layout_h = QHBoxLayout()
        if opacity:
            layout_h.addWidget(QLabel('Opac'))
            layout_h.addWidget(self.__opacity)
        if gamma:
            layout_h.addWidget(QLabel('Gam'))
            layout_h.addWidget(self.__gamma)
        if reverse:
            layout_h.addWidget(self.__check)
        if log:
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
        return _cmapdic[self.currentColor()]

    def isLog(self):
        return self.__log.isChecked()

    def setLog(self, value):
        self.__log.setChecked(value)

    def setOpacity(self, value):
        self.__opacity.setValue(value)

    def opacity(self):
        return self.__opacity.value()

    def setGamma(self, value):
        self.__gamma.setValue(value)

    def gamma(self):
        return self.__gamma.value()