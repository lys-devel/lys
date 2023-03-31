
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
        """Reimplementation of textFromValue"""
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
        """Reimplementation of stepBy"""
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
    """
    A widget to select color.
    """
    colorChanged = QtCore.pyqtSignal(object)
    """Emitted when the selected color is changed"""

    def __init__(self):
        super().__init__()
        self.clicked.connect(self._onClicked)
        self.__color = "black"

    def _onClicked(self):
        res = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.getColor()))
        if res.isValid():
            self.setColor(res.name())
            self.colorChanged.emit(self.getColor())

    def setColor(self, color):
        """
        Set the color.

        Args:
            color(str): The color string such as '#112233'.
        """
        if isinstance(color, tuple) or isinstance(color, list):
            if len(color) == 4:
                self.__color = "rgba" + str((int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), int(color[3])))
            if len(color) == 3:
                self.__color = "rgba" + str((color[0] * 255, color[1] * 255, color[2] * 255, 1))
        else:
            self.__color = color
        self.setStyleSheet("background-color:" + self.__color)

    def getColor(self):
        """
        Get the color.

        Returns:
            str: The color string such as '#112233'
        """
        return self.__color

    def getColorAsArray(self):
        """
        Get the color as QtGui.QColor.

        Returns:
            QColor: The color selected by user.
        """
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
    """
    A widget to select colormap.

    Args:
        opacity(bool): If True, the opacity setting is enabled.
        log(bool): If True, 'log' checkbox is enabled.
        reverse(bool): If True, 'reverse' checkbox is enabled.
        gamma(bool): If True, gamma value can be set.
    """
    colorChanged = QtCore.pyqtSignal()
    """Emitted when the color map is changed"""

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

    def setEnabled(self, enable):
        """
        Enable the widget.

        Args:
            enable(bool): The boolean to specify whether enabling or disabling the widget
        """
        self.__combo.setEnabled(enable)
        self.__opacity.setEnabled(enable)
        self.__gamma.setEnabled(enable)
        self.__check.setEnabled(enable)
        self.__log.setEnabled(enable)

    def __changed(self):
        self.colorChanged.emit()

    def setColormap(self, cmap):
        """
        Set the colormap.

        Args:
            cmap(str): The name of matplotlib colormaps. Use matplotlib.pyplot.colormaps to view all colormap names.
        """
        tmp = cmap.split('_')
        self.__combo.setColormap(tmp[0])
        self.__check.setChecked(not len(tmp) == 1)

    def currentColor(self):
        """
        Get the name of the selected colormap.

        Returns:
            str: The name of the selected colormap.
        """
        if self.__check.isChecked():
            return self.__combo.currentText() + "_r"
        else:
            return self.__combo.currentText()

    def currentColorMaps(self):
        """
        Get the QtGui.QPixmap of the selected colormap.

        Returns:
            QPixmap: The selected colormap.
        """
        return _cmapdic[self.currentColor()]

    def isLog(self):
        """
        Check if the 'log' checkbox is checked.

        Returns:
            bool: Whether the 'log' checkbox is checked.
        """
        return self.__log.isChecked()

    def setLog(self, value):
        """
        Set the state of the 'log' checkbox.

        Args:
            value(bool): True to check 'log' checkbox.
        """
        self.__log.setChecked(value)

    def setOpacity(self, value):
        """
        Set the opacity of the colormap.

        Args:
            value(float): The opacity between 0 to 1.
        """
        self.__opacity.setValue(value)

    def opacity(self):
        """
        Get the opacity.

        Returns:
            float: The value of opacity.
        """
        return self.__opacity.value()

    def setGamma(self, value):
        """
        Set the gamma of the colormap.

        Args:
            value(float): The gamma value.
        """
        self.__gamma.setValue(value)

    def gamma(self):
        """
        Get the gamma.

        Returns:
            float: The value of gamma.
        """
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
    """
    A layout that specifies the kernel size of convolution filter (such as median filter).

    Args:
        dimension(int): The dimension of the kernel.
        odd(bool): If True, only odd values can be set.
    """

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
        """
        Get kernel size as array.

        Returns:
            list: The kernel size.
        """
        return [k.value() for k in self._kernels]

    def setKernelSize(self, val):
        """
        Set kernel size.

        Args:
            val(list of integers): The kernel size.
        """
        for k, v in zip(self._kernels, val):
            k.setValue(v)


class kernelSigmaLayout(QtWidgets.QGridLayout):
    """
    A layout that specifies the kernel of gaussian convolution filter.

    Args:
        dimension(int): The dimension of the kernel.
    """

    def __init__(self, dimension=2):
        super().__init__()
        self.addWidget(QtWidgets.QLabel('Sigma'), 1, 0)
        self._kernels = [ScientificSpinBox() for d in range(dimension)]
        for i, k in enumerate(self._kernels):
            k.setMinimum(0)
            self.addWidget(QtWidgets.QLabel('Axis' + str(i + 1)), 0, i + 1)
            self.addWidget(k, 1, i + 1)

    def getKernelSigma(self):
        """
        Get kernel sigma as array.

        Returns:
            list: The kernel sigma.
        """
        return [k.value() for k in self._kernels]

    def setKernelSigma(self, val):
        """
        Set kernel sigma.

        Args:
            val(list of float): The kernel sigma.
        """
        for k, v in zip(self._kernels, val):
            k.setValue(v)


class AxisCheckLayout(QtWidgets.QHBoxLayout):
    """
    A layout that specifies axes.

    Args:
        dim(int): The dimension of data.
    """
    stateChanged = QtCore.pyqtSignal()
    """
    Emitted when the state of the layout is changed.
    """

    def __init__(self, dim):
        super().__init__()
        self._axes = [QtWidgets.QCheckBox("Axis" + str(i)) for i in range(dim)]
        for a in self._axes:
            a.stateChanged.connect(self.stateChanged)
            self.addWidget(a)

    def GetChecked(self):
        """
        Return checked axes as array.

        Returns:
            list of integers: The selected axes
        """
        axes = []
        for i, a in enumerate(self._axes):
            if a.isChecked():
                axes.append(i)
        return axes

    def SetChecked(self, axes):
        """
        Set the state of the layout.

        Args:
            axes(list of integers): The list of axes to be checked.
        """
        for i, a in enumerate(self._axes):
            if i in axes:
                a.setChecked(True)
            else:
                a.setChecked(False)


class AxisSelectionLayout(QtWidgets.QHBoxLayout):
    """
    A layout to specify an axis.

    Args:
        label(str): The label of the layout.
        dim(int): The dimension of data.
        init(int): The axis initially selected.
    """

    axisChanged = QtCore.pyqtSignal()
    """Emitted when the selected axis is changed."""

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
        self.childs = [QtWidgets.QRadioButton(str(i + 1)) for i in range(self.dimension)]
        for c in self.childs:
            self.addWidget(c)
            self.group.addButton(c)
            c.toggled.connect(self.axisChanged)

    def setDimension(self, d):
        """
        Change the dimension of the layout.

        Args:
            d(int): The new dimension
        """
        if d == self.dimension:
            return
        self.dimension = d
        self.__update()

    def getAxis(self):
        """
        Get the selected axis.

        Returns:
            int: The selected axis.
        """
        for i, b in enumerate(self.childs):
            if b.isChecked():
                return i

    def setAxis(self, axis):
        """
        Set the selected axis.

        Args:
            axis(int): The axis to select.
        """
        self.group.setExclusive(False)
        for c in self.childs:
            c.setChecked(False)
        self.childs[axis].setChecked(True)
        self.group.setExclusive(True)

    def setEnabled(self, enabled):
        """
        Enable the widgets in this layout.

        Args:
            enabled(bool): Whether the widgets are enabled.
        """
        for c in self.childs:
            c.setEnabled(enabled)


class AxesSelectionDialog(QtWidgets.QDialog):
    """
    A dialog to select two axes.

    Args:
        dim(int): The dimension of the data.
    """

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
        """
        Change the dimension.

        Args:
            d(int): The new dimension
        """
        self.axis1.setDimension(n)
        self.axis2.setDimension(n)

    def getAxes(self):
        """
        Get axes selected.

        Returns:
            tuple of length 2: The selected axes
        """
        return (self.axis1.getAxis(), self.axis2.getAxis())


class RegionSelectWidget(QtWidgets.QGridLayout):
    """
    A widget to select region of multi-dimensional data.
    Args:
        parent: The parent widget.
        dim: The dimension of the data.
        check: If True, user can select the axes.
    """
    stateChanged = QtCore.pyqtSignal()
    """
    Emitted when the state of the checkbox is changed.
    """

    def __init__(self, parent, dim, check=False):
        super().__init__()
        self.dim = dim
        self._check = check
        self.__initLayout(dim)

    def __initLayout(self, dim):
        self.__loadPrev = QtWidgets.QPushButton('Load from Graph', clicked=self.__load)
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
        """
        Set the region.

        Args:
            axis(int): The axis to be changed.
            range(length 2 sequency): The range to be set.
        """
        if axis < len(self.start):
            self.start[axis].setValue(min(range[0], range[1]))
            self.end[axis].setValue(max(range[0], range[1]))

    def getRegion(self):
        """
        Get the specified region.

        Returns:
            list of length 2 sequence: The specified region.
        """
        return [[s.value(), e.value()] for s, e in zip(self.start, self.end)]

    def setChecked(self, checked):
        """
        Set the state of the checkboxes.

        Args:
            checked(list of boolean): The state to be set.
        """
        for wid, c in zip(self._checkWidgets, checked):
            wid.setChecked(c)

    def getChecked(self):
        """
        Get the state of the checkboxes.

        Reutrns:
            list of boolean: The state of the checkboxes.
        """
        return [s.isChecked() for s in self._checkWidgets]


class IndiceSelectionLayout(QtWidgets.QGridLayout):
    """
    A layout to specify indice.

    Args:
        shape(tuple): The shape of data.
    """

    valueChanged = QtCore.pyqtSignal()
    """
    Emitted when the value is changed.
    """

    def __init__(self, shape=None):
        super().__init__()
        self._shape = None
        self._childs = []
        self.setShape(shape)

    def __update(self):
        for c in self._childs:
            self.removeWidget(c)
            c.deleteLater()
        labels = [QtWidgets.QLabel("Axis" + str(i)) for i in range(len(self._shape))]
        self._childs = [QtWidgets.QSpinBox() for i in range(len(self._shape))]
        for i, c in enumerate(labels):
            self.addWidget(c, 0, i)
        for i, c in enumerate(self._childs):
            c.setRange(0, self._shape[i] - 1)
            c.valueChanged.connect(self.valueChanged)
            self.addWidget(c, 1, i)

    def setShape(self, shape):
        """
        Change the shape of the layout.

        Args:
            shape(tuple): The new shape
        """
        if shape == self._shape:
            return
        self._shape = shape
        self.__update()

    def getIndices(self):
        """
        Get the indices.

        Returns:
            sequence of int: The indices.
        """
        return tuple([c.value() for c in self._childs])

    def setValues(self, indices):
        """
        Set the indices.

        Args:
            indices(sequence of int): The indices.
        """
        for c, i in zip(self._childs, indices):
            c.setValue(i)

    def setEnabled(self, enabled):
        """
        Enable the respective spin box.

        Args:
            enabled(sequence of boolean): Whether the spin box is enabled.
        """
        for c, e in zip(self._childs, enabled):
            c.setEnabled(e)
