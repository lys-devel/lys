import numpy as np
import dask.array as da
import itertools

from lys import DaskWave
from lys.Qt import QtWidgets
from lys.filters import FilterInterface, FilterSettingBase, filterGUI, addFilter

from .CommonWidgets import kernelSizeLayout, AxisCheckLayout, ScientificSpinBox


class ReduceSizeFilter(FilterInterface):
    """
    Reduce size of data.

    When *kernel* = (xn,yn), shape of data is reduced to 1/xn and 1/yn along both x and y direction, respectively. 

    This filter is used to gain signal to noise ratio by summation.

    Args:
        kernel(sequence of int): see above description.

    Example:

        Sum 2*2 data::

            w = Wave(np.ones([6, 6]), [0, 1, 2, 3, 4, 5], [0, 1, 2, 3, 4, 5])
            f = filters.ReduceSizeFilter(kernel=(2, 2))
            result = f.execute(w)
            print(result.shape)
            # (3, 3)
            print(result.x)
            # [0, 2, 4]
    """

    def __init__(self, kernel):
        self.kernel = kernel

    def _execute(self, wave, *args, **kwargs):
        axes = []
        for i, k in enumerate(self.kernel):
            a = wave.axes[i]
            if (a == np.array(None)).all():
                axes.append(a)
            else:
                axes.append(wave.axes[i][0::k])
        res = []
        rans = [range(k) for k in self.kernel]
        for list in itertools.product(*rans):
            sl = tuple([slice(x, None, step) for x, step in zip(list, self.kernel)])
            res.append(wave.data[sl])
        res = da.mean(da.stack(res), axis=0)
        return DaskWave(res, *axes, **wave.note)

    def getParameters(self):
        return {"kernel": self.kernel}


class PaddingFilter(FilterInterface):
    """
    Add value at the edge of data

    Args:
        axes(list of int): axes to be padded.
        value(float): value to be added.
        size(int): size of padding.
        position('first' or 'last' or 'both'): position of padding.

    Example:

        Add zero at the left edge of data::

            w = Wave([1, 2, 3], [0, 1, 2])
            f = filters.PaddingFilter(axes=[0], value=0, size=2, position="first")
            result = f.execute(w)
            print(result.data)
            # [0, 0, 1, 2, 3]
            print(result.x)
            # [-2, -1, 0, 1, 2]
    """

    def __init__(self, axes, value=0, size=100, position="first"):
        self.axes = axes
        self.size = size
        self.value = value
        self.direction = position

    def _execute(self, wave, *args, **kwargs):
        axes = [self._createAxis(wave, ax) for ax in self.axes]
        data = wave.data
        for ax in self.axes:
            data = self._createData(data, ax)
            data = da.concatenate(data, axis=ax)
        return DaskWave(data, *axes, **wave.note)

    def _createData(self, data, ax):
        shape = list(data.shape)
        shape[ax] = self.size
        pad = da.ones(shape) * self.value
        if self.direction == "first":
            data = [pad, data]
        elif self.direction == "last":
            data = [data, pad]
        else:
            data = [pad, data, pad]
        return data

    def _createAxis(self, wave, ax):
        if wave.axisIsValid(ax):
            axis_old = wave.getAxis(ax)
        else:
            return None
        s = axis_old[0]
        e = axis_old[-1]
        newlen = len(axis_old) + self.size
        d = (e - s) / (len(axis_old) - 1) * (newlen - 1)
        if self.direction == "first":
            axis_new = np.linspace(e - d, e, newlen)
        elif self.direction == "last":
            axis_new = np.linspace(s, s + d, newlen)
        else:
            axis_new = np.linspace(e - d, s + d, len(axis_old) + 2 * self.size)
        return axis_new

    def getParameters(self):
        return {"axes": self.axes, "value": self.value, "size": self.size, "position": self.direction}


@filterGUI(ReduceSizeFilter)
class _ReduceSizeSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = kernelSizeLayout(dimension, odd=False)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"kernel": self._layout.getKernelSize()}

    def setParameters(self, kernel):
        self._layout.setKernelSize(kernel)


@filterGUI(PaddingFilter)
class _PaddingSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._axes = AxisCheckLayout(dimension)
        self._size = QtWidgets.QSpinBox()
        self._size.setRange(1, 100000)
        self._size.setValue(200)
        self._value = ScientificSpinBox()
        self._direction = QtWidgets.QComboBox()
        self._direction.addItems(["first", "last", "both"])
        self._layout = QtWidgets.QGridLayout()
        self._layout.addWidget(QtWidgets.QLabel("axes"), 0, 0)
        self._layout.addWidget(QtWidgets.QLabel("direction"), 0, 1)
        self._layout.addWidget(QtWidgets.QLabel("size"), 0, 2)
        self._layout.addWidget(QtWidgets.QLabel("value"), 0, 3)
        self._layout.addLayout(self._axes, 1, 0)
        self._layout.addWidget(self._direction, 1, 1)
        self._layout.addWidget(self._size, 1, 2)
        self._layout.addWidget(self._value, 1, 3)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"axes": self._axes.GetChecked(), "value": self._value.value(), "size": self._size.value(), "position": self._direction.currentText()}

    def setParameters(self, axes, value, size, position):
        self._axes.SetChecked(axes)
        self._size.setValue(size)
        self._value.setValue(value)
        if position == "first":
            self._direction.setCurrentIndex(0)
        else:
            self._direction.setCurrentIndex(1)


addFilter(ReduceSizeFilter, gui=_ReduceSizeSetting, guiName="Reduce size", guiGroup="Resize and interpolation")
addFilter(PaddingFilter, gui=_PaddingSetting, guiName="Padding", guiGroup="Resize and interpolation")
