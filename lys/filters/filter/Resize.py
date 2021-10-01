import numpy as np
import dask.array as da
import itertools
from lys import Wave, DaskWave
from .FilterInterface import FilterInterface


class ReduceSizeFilter(FilterInterface):
    def __init__(self, kernel):
        self.kernel = kernel

    def _execute(self, wave, **kwargs):
        axes = []
        for i, k in enumerate(self.kernel):
            a = wave.axes[i]
            if (a == np.array(None)).all():
                axes.append(a)
            else:
                axes.append(wave.axes[i][0::k])
        res = None
        rans = [range(k) for k in self.kernel]
        for list in itertools.product(*rans):
            sl = tuple([slice(x, None, step) for x, step in zip(list, self.kernel)])
            if res is None:
                res = wave.data[sl]
            else:
                res += wave.data[sl]
        wave.data = res
        wave.axes = axes
        return wave

    def getKernel(self):
        return self.kernel


class PaddingFilter(FilterInterface):
    def __init__(self, axes, value=0, size=100, direction="first"):
        self.axes = axes
        self.size = size
        self.value = value
        self.direction = direction

    def _execute(self, wave, **kwargs):
        if isinstance(wave, Wave):
            lib = np
        elif isinstance(wave, DaskWave):
            lib = da
        for ax in self.axes:
            data = self._createData(wave, ax, lib)
            axis = self._createAxis(wave, ax)
            wave.data = lib.concatenate(data, axis=ax)
            wave.axes[ax] = axis
        return wave

    def _createData(self, wave, ax, lib):
        shape = list(wave.data.shape)
        shape[ax] = self.size
        pad = lib.ones(shape) * self.value
        if self.direction == "first":
            data = [pad, wave.data]
        elif self.direction == "last":
            data = [wave.data, pad]
        else:
            data = [pad, wave.data, pad]
        return data

    def _createAxis(self, wave, ax):
        if wave.axisIsValid(ax):
            axis_old = np.array(wave.axes[ax])
        else:
            return None
        s = axis_old[0]
        e = axis_old[len(axis_old) - 1]
        d = (e - s) / len(axis_old) * (len(axis_old) + self.size)
        if self.direction == "first":
            axis_new = np.linspace(e - d, e, len(axis_old) + self.size)
        elif self.direction == "last":
            axis_new = np.linspace(s, s + d, len(axis_old) + self.size)
        else:
            axis_new = np.linspace(e - d, s + d, len(axis_old) + 2 * self.size)
        return axis_new

    def getParams(self):
        return self.axes, self.value, self.size, self.direction
