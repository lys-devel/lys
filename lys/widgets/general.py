
import math
import numpy as np
from matplotlib import cm

from lys import frontCanvas
from lys.Qt import QtCore, QtWidgets, QtGui


class ScientificSpinBox(QtWidgets.QDoubleSpinBox):
    """
    Spin box that displays values in sdientific notation, which is frequently used in lys.
    """

    def __init__(self, *args, valueChanged=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setRange(-np.inf, np.inf)
        self.setDecimals(128)
        self.setAccelerated(True)
        if valueChanged is not None:
            self.valueChanged.connect(valueChanged)

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
            return (QtGui.QValidator.Intermediate, text, pos)
        else:
            return (QtGui.QValidator.Acceptable, text, pos)

    def stepBy(self, steps):
        """stepBy"""
        v = self.value()
        if v == 0:
            n = 1
        else:
            val = np.log10(abs(v))
            p = math.floor(val)
            a = np.round(v / 10**p, 5)
            if int(a) == 10:
                a = 1
                p = p - 1
            p = p - 1
            if abs(abs(a) - 1) < 1e-5 and steps * a < 0:
                p = p - 1
            n = 10 ** p
            if steps * a > 0:
                if 2 <= abs(a) < 3:
                    n *= 2
                elif 3 <= abs(a) < 5:
                    n *= 4
                elif abs(a) >= 5:
                    n *= 5
            else:
                if 2 < abs(a) <= 3:
                    n *= 2
                elif 3 < abs(a) <= 5:
                    n *= 4
                elif abs(a) > 5 or abs(abs(a) - 1) < 1e-5:
                    n *= 5
        self.setValue(v + steps * n)


class ColorSelection(QtWidgets.QPushButton):
    colorChanged = QtCore.pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.clicked.connect(self.OnClicked)
        self.__color = "black"

    def OnClicked(self):
        res = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.getColor()))
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
        return QtGui.QColor(self.getColor())


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
    rgbas = [QtGui.QColor(int(r * 255), int(g * 255), int(b * 255), int(a * 255)).rgba() for r, g, b, a in rgbas]
    im = QtGui.QImage(steps, 1, QtGui.QImage.Format_Indexed8)
    im.setColorTable(rgbas)
    for i in range(steps):
        im.setPixel(i, 0, i)
    im = im.scaled(100, 15)
    pm = QtGui.QPixmap.fromImage(im)
    return pm


def _loadCmaps():
    for item in _cmaps:
        for i in item[1]:
            _cmapdic[i] = _cmap2pixmap(i)


_loadCmaps()


class ColormapSelection(QtWidgets.QWidget):
    colorChanged = QtCore.pyqtSignal()

    class _ColorCombo(QtWidgets.QComboBox):
        def __init__(self):
            super().__init__()
            model = QtGui.QStandardItemModel()
            self.setModel(model)
            self.__list = []
            n = 0
            for item in _cmaps:
                for i in item[1]:
                    data = QtGui.QStandardItem(i)
                    data.setData(_cmapdic[i], QtCore.Qt.DecorationRole)
                    model.setItem(n, data)
                    self.__list.append(i)
                    n += 1

        def setColormap(self, cmap):
            self.setCurrentIndex(self.__list.index(cmap))

    def __init__(self, opacity=True, log=True, reverse=True, gamma=True):
        super().__init__()
        self.__combo = ColormapSelection._ColorCombo()
        self.__combo.activated.connect(self.__changed)
        self.__opacity = QtWidgets.QDoubleSpinBox()
        self.__opacity.setRange(0, 1)
        self.__opacity.setSingleStep(0.1)
        self.__opacity.setDecimals(2)
        self.__opacity.valueChanged.connect(self.__changed)
        self.__gamma = ScientificSpinBox()
        self.__gamma.setRange(0, 1000)
        self.__gamma.setDecimals(2)
        self.__gamma.valueChanged.connect(self.__changed)
        self.__check = QtWidgets.QCheckBox("Rev")
        self.__check.stateChanged.connect(self.__changed)
        self.__log = QtWidgets.QCheckBox("Log")
        self.__log.stateChanged.connect(self.__changed)
        layout = QtWidgets.QVBoxLayout()

        layout_h = QtWidgets.QHBoxLayout()
        if opacity:
            layout_h.addWidget(QtWidgets.QLabel('Opac'))
            layout_h.addWidget(self.__opacity)
        if gamma:
            layout_h.addWidget(QtWidgets.QLabel('Gam'))
            layout_h.addWidget(self.__gamma)
        if reverse:
            layout_h.addWidget(self.__check)
        if log:
            layout_h.addWidget(self.__log)

        layout.addLayout(layout_h)
        layout.addWidget(self.__combo)
        self.setLayout(layout)

    def setEnabled(self, b):
        self.__combo.setEnabled(b)
        self.__opacity.setEnabled(b)
        self.__gamma.setEnabled(b)
        self.__check.setEnabled(b)
        self.__log.setEnabled(b)

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


class _SpinBoxOverOne(QtWidgets.QSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimum(1)
        self.setValue(1)


class _OddSpinBox(QtWidgets.QSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimum(1)
        self.setSingleStep(2)
        self.setValue(3)
        self.valueChanged.connect(self.valChanged)

    def valChanged(self, val):
        if val % 2 == 0:
            self.setValue(val - 1)


class kernelSizeLayout(QtWidgets.QGridLayout):
    def __init__(self, dimension=2, odd=True):
        super().__init__()
        self.addWidget(QtWidgets.QLabel('Kernel Size'), 1, 0)
        if odd:
            spin = _OddSpinBox
        else:
            spin = _SpinBoxOverOne
        self._kernels = [spin() for d in range(dimension)]
        for i, k in enumerate(self._kernels):
            self.addWidget(QtWidgets.QLabel('Axis' + str(i + 1)), 0, i + 1)
            self.addWidget(k, 1, i + 1)

    def getKernelSize(self):
        return [k.value() for k in self._kernels]

    def setKernelSize(self, val):
        for k, v in zip(self._kernels, val):
            k.setValue(v)


class kernelSigmaLayout(QtWidgets.QGridLayout):
    def __init__(self, dimension=2):
        super().__init__()
        self.addWidget(QtWidgets.QLabel('Sigma'), 1, 0)
        self._kernels = [ScientificSpinBox() for d in range(dimension)]
        for i, k in enumerate(self._kernels):
            k.setMinimum(0)
            self.addWidget(QtWidgets.QLabel('Axis' + str(i + 1)), 0, i + 1)
            self.addWidget(k, 1, i + 1)

    def getKernelSigma(self):
        return [k.value() for k in self._kernels]

    def setKernelSigma(self, val):
        for k, v in zip(self._kernels, val):
            k.setValue(v)


class AxisCheckLayout(QtWidgets.QHBoxLayout):
    stateChanged = QtCore.pyqtSignal()

    def __init__(self, dim):
        super().__init__()
        self._axes = [QtWidgets.QCheckBox("Axis" + str(i)) for i in range(dim)]
        for a in self._axes:
            a.stateChanged.connect(self.stateChanged)
            self.addWidget(a)

    def GetChecked(self):
        axes = []
        for i, a in enumerate(self._axes):
            if a.isChecked():
                axes.append(i)
        return axes

    def SetChecked(self, axes):
        for i, a in enumerate(self._axes):
            if i in axes:
                a.setChecked(True)
            else:
                a.setChecked(False)


class AxisSelectionLayout(QtWidgets.QHBoxLayout):
    def __init__(self, label, dim=2, init=0):
        super().__init__()
        self.dimension = 0
        self.group = QtWidgets.QButtonGroup()
        self.childs = []
        self.addWidget(QtWidgets.QLabel(label))
        self.setDimension(dim)
        if init >= len(self.childs):
            init = 0
        self.childs[init].setChecked(True)

    def __update(self):
        for c in self.childs:
            self.removeWidget(c)
            self.group.removeButton(c)
            c.deleteLater()
        self.childs = [QtWidgets.QRadioButton(str(i)) for i in range(self.dimension)]
        for c in self.childs:
            self.addWidget(c)
            self.group.addButton(c)

    def setDimension(self, n):
        if n == self.dimension:
            return
        self.dimension = n
        self.__update()

    def getAxis(self):
        for i, b in enumerate(self.childs):
            if b.isChecked():
                return i

    def setAxis(self, axis):
        self.group.setExclusive(False)
        for c in self.childs:
            c.setChecked(False)
        self.childs[axis].setChecked(True)
        self.group.setExclusive(True)


class AxesSelectionDialog(QtWidgets.QDialog):
    def __init__(self, dim=2):
        super().__init__()
        self.dim = dim
        self.__initlayout()
        self.show()

    def __initlayout(self):
        self.axis1 = AxisSelectionLayout("Axis 1", self.dim, 0)
        self.axis2 = AxisSelectionLayout("Axis 2", self.dim, 1)
        ok = QtWidgets.QPushButton("O K", clicked=self.accept)
        cancel = QtWidgets.QPushButton("CALCEL", clicked=self.close)
        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(ok)
        h1.addWidget(cancel)
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.axis1)
        layout.addLayout(self.axis2)
        layout.addLayout(h1)
        self.setLayout(layout)

    def setDimension(self, n):
        self.axis1.setDimension(n)
        self.axis2.setDimension(n)

    def getAxes(self):
        return (self.axis1.getAxis(), self.axis2.getAxis())


class RegionSelectWidget(QtWidgets.QGridLayout):
    loadClicked = QtCore.pyqtSignal(object)
    stateChanged = QtCore.pyqtSignal()

    def __init__(self, parent, dim, loader=None, check=False):
        super().__init__()
        self.dim = dim
        self.loader = loader
        self._check = check
        self.__initLayout(dim, loader)

    def __initLayout(self, dim, loader):
        self.__loadPrev = QtWidgets.QPushButton('Load from Graph', clicked=self.__loadFromPrev)
        if loader is None:
            self.loadClicked.connect(self.__load)
        else:
            self.loadClicked.connect(loader)
        self.addWidget(self.__loadPrev, 0, 0)

        self.addWidget(QtWidgets.QLabel("from"), 1, 0)
        self.addWidget(QtWidgets.QLabel("to"), 2, 0)
        self.start = [ScientificSpinBox() for d in range(dim)]
        self.end = [ScientificSpinBox() for d in range(dim)]
        i = 1
        self._checkWidgets = []
        for s, e in zip(self.start, self.end):
            if self._check:
                check = QtWidgets.QCheckBox("Axis" + str(i))
                check.stateChanged.connect(self.stateChanged)
            else:
                check = QtWidgets.QLabel("Axis" + str(i))
            self._checkWidgets.append(check)
            self.addWidget(check, 0, i)
            self.addWidget(s, 1, i)
            self.addWidget(e, 2, i)
            i += 1

    def __loadFromPrev(self, arg):
        self.loadClicked.emit(self)

    def __load(self, obj):
        c = frontCanvas()
        if c is not None:
            r = c.selectedRange()
            if self.dim == 2:
                self.setRegion(0, (r[0][0], r[1][0]))
                self.setRegion(1, (r[0][1], r[1][1]))
            else:
                d = AxesSelectionDialog(self.dim)
                value = d.exec_()
                if value:
                    ax = d.getAxes()
                    self.setRegion(ax[0], (r[0][0], r[1][0]))
                    self.setRegion(ax[1], (r[0][1], r[1][1]))

    def setRegion(self, axis, range):
        if axis < len(self.start):
            self.start[axis].setValue(min(range[0], range[1]))
            self.end[axis].setValue(max(range[0], range[1]))

    def getRegion(self):
        return [[s.value(), e.value()] for s, e in zip(self.start, self.end)]

    def setChecked(self, checked):
        for wid, c in zip(self._checkWidgets, checked):
            wid.setChecked(c)

    def getChecked(self):
        return [s.isChecked() for s in self._checkWidgets]
