from scipy.ndimage import interpolation
import numpy as np
import dask.array as da

from lys import DaskWave
from lys.filters import FilterSettingBase, filterGUI, addFilter

from .FilterInterface import FilterInterface
from .CommonWidgets import QGridLayout, QSpinBox, QLabel, AxisCheckLayout, QHBoxLayout, QComboBox


class ShiftFilter(FilterInterface):
    """
    Shift data by scipy.ndimage.interpolation.shift.

    Args:
        shift(tuple of float): The shift along the axes.
    """

    def __init__(self, shift=None):
        self._s = shift

    def _execute(self, wave, *args, shift=None, **kwargs):
        order = 1
        if shift is None:
            shi = list(self._s)
        else:
            shi = list(shift)
        for i, s in enumerate(shi):
            ax = wave.getAxis(i)
            dx = (ax[-1] - ax[0]) / (len(ax) - 1)
            shi[i] = shi[i] / dx
        data = wave.data
        for ax, s in enumerate(shi):
            data = da.apply_along_axis(interpolation.shift, ax, data.astype(float), s, dtype=float, shape=(data.shape[ax],), order=order, cval=0)
        return DaskWave(data, *wave.axes, **wave.note)

    def getParameters(self):
        return {"shift": self._s}


class ReverseFilter(FilterInterface):
    """
    Reverse data by dask.array.flip

    Args:
        axes(list of int): axes to be reversed.
    """

    def __init__(self, axes):
        self.axes = axes

    def _execute(self, wave, *args, **kwargs):
        data = wave.data
        for a in self.axes:
            data = da.flip(data, a)
        return DaskWave(data, *wave.axes, **wave.note)

    def getParameters(self):
        return {"axes": self.axes}


class RollFilter(FilterInterface):
    """
    Reverse data by dask.array.roll

    Args:
        amount('1/2' or '1/4' or '-1/4'): amount of roll.
        axes(list of int): axes to be rolled.
    """

    def __init__(self, amount, axes):
        self.axes = axes
        self.amount = amount

    def _execute(self, wave, *args, **kwargs):
        data = wave.data
        for a in self.axes:
            if self.amount == "1/2":
                amount = data.shape[a] / 2
            if self.amount == "1/4":
                amount = data.shape[a] / 4
            if self.amount == "-1/4":
                amount = -data.shape[a] / 4
            data = da.roll(data, amount, axis=a)
        return DaskWave(data, *wave.axes, **wave.note)

    def getParameters(self):
        return {"amount": self.amount, "axes": self.axes}


class ReflectFilter(FilterInterface):
    """
    Reflect data.

    type('center' or 'first' or 'last'): specifies where the data is reflected.
    axes(tuple of int): specifies axes reflected.
    """

    def __init__(self, type, axes):
        self.axes = axes
        self.type = type

    def _execute(self, wave, *args, **kwargs):
        data = wave.data
        axes = list(wave.axes)
        for a in self.axes:
            sl = [slice(None)] * data.ndim
            sl[a] = slice(None, None, -1)
            if self.type == "center":
                data = data + data[tuple(sl)]
            if self.type == "first":
                data = da.concatenate([data[tuple(sl)], data], axis=a)
                axes[a] = self._elongateAxis(axes[a], self.type)
            if self.type == "last":
                data = da.concatenate([data, data[tuple(sl)]], axis=a)
                axes[a] = self._elongateAxis(axes[a], self.type)
        return DaskWave(data, *axes, **wave.note)

    def _elongateAxis(self, axis, type):
        if axis is None:
            return None
        start = axis[0]
        end = axis[len(axis) - 1]
        d = (end - start) / (len(axis) - 1)
        if type == "last":
            return np.linspace(start, start + d * (2 * len(axis) - 1), 2 * len(axis))
        if type == "first":
            return np.linspace(end - d * (2 * len(axis) - 1), end, 2 * len(axis))

    def getParameters(self):
        return {"type": self.type, "axes": self.axes}


@filterGUI(ShiftFilter)
class _ImageShiftSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = QGridLayout()
        self._dim = dimension
        self._values = []
        for i in range(dimension):
            wid = QSpinBox()
            wid.setRange(-1000000, 1000000)
            self._values.append(wid)
            self._layout.addWidget(QLabel('Axis' + str(i + 1)), 0, i)
            self._layout.addWidget(wid, 1, i)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"shift": [v.value() for v in self._values]}

    def setParameters(self, shift):
        for ax, s in enumerate(shift):
            self._values[ax].setValue(s)


@filterGUI(ReverseFilter)
class _ReverseSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self._axes = AxisCheckLayout(dim)
        self.setLayout(self._axes)

    def getParameters(self):
        return {"axes": self._axes.GetChecked()}

    def setParameters(self, axes):
        self._axes.SetChecked(axes)


@filterGUI(RollFilter)
class _RollSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        layout = QHBoxLayout()
        self._combo = QComboBox()
        self._combo.addItems(["1/2", "1/4", "-1/4"])
        self._axes = AxisCheckLayout(dim)
        layout.addWidget(self._combo)
        layout.addLayout(self._axes)
        self.setLayout(layout)

    def getParameters(self):
        return {"amount": self._combo.currentText(), "axes": self._axes.GetChecked()}

    def setParameters(self, amount, axes):
        self._axes.SetChecked(axes)
        self._combo.setCurrentText(amount)


@ filterGUI(ReflectFilter)
class _ReflectSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        layout = QHBoxLayout()
        self._combo = QComboBox()
        self._combo.addItem("first")
        self._combo.addItem("last")
        self._combo.addItem("center")
        self._axes = AxisCheckLayout(dim)
        layout.addWidget(self._combo)
        layout.addLayout(self._axes)
        self.setLayout(layout)

    def getParameters(self):
        return {"type": self._combo.currentText(), "axes": self._axes.GetChecked()}

    def setParameters(self, type, axes):
        self._axes.SetChecked(axes)
        self._combo.setCurrentText(type)


addFilter(ShiftFilter, gui=_ImageShiftSetting, guiName="Shift image", guiGroup="Image transformation")

addFilter(ReverseFilter, gui=_ReverseSetting, guiName="Reverse", guiGroup="Symmetric operation")
addFilter(RollFilter, gui=_RollSetting, guiName="Roll", guiGroup="Symmetric operation")
addFilter(ReflectFilter, gui=_ReflectSetting, guiName="Reflect", guiGroup="Symmetric operation")
