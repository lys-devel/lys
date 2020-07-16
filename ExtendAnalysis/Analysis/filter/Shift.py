import scipy
import numpy as np
import dask.array as da
from dask.array import flip, roll

from ExtendAnalysis import Wave, DaskWave
from .FilterInterface import FilterInterface


class ShiftFilter(FilterInterface):
    def __init__(self, shift=None):
        self._s = shift

    def _execute(self, wave, shift=None, **kwargs):
        if wave.data.ndim > 3:
            order = 0
        else:
            order = 3
        if shift is None:
            shi = self._s
        else:
            shi = shift
        if isinstance(wave, Wave):
            if shift is None:
                wave.data = (scipy.ndimage.interpolation.shift(np.array(wave.data, dtype=np.float32), self._s[0:wave.data.ndim], order=order, cval=0))
            else:
                wave.data = (scipy.ndimage.interpolation.shift(np.array(wave.data, dtype=np.float32), shift[0:wave.data.ndim], order=order, cval=0))
        elif isinstance(wave, DaskWave):
            for ax, s in enumerate(shi):
                wave.data = da.apply_along_axis(scipy.ndimage.interpolation.shift, ax, wave.data, s, dtype=wave.data.dtype, shape=(wave.data.shape[ax],), order=order, cval=0)

    def getParams(self):
        return self._s


class ReverseFilter(FilterInterface):
    def __init__(self, axes):
        self.axes = axes

    def _execute(self, wave, **kwargs):
        for a in self.axes:
            if isinstance(wave, Wave):
                wave.data = np.flip(wave.data, a)
            else:
                wave.data = flip(wave.data, a)
        return wave

    def getAxes(self):
        return self.axes


class RollFilter(FilterInterface):
    def __init__(self, amount, axes):
        self.axes = axes
        self.amount = amount

    def _execute(self, wave, **kwargs):
        for a in self.axes:
            if self.amount == "1/2":
                amount = wave.data.shape[a] / 2
            if self.amount == "1/4":
                amount = wave.data.shape[a] / 4
            if self.amount == "-1/4":
                amount = -wave.data.shape[a] / 4
            if isinstance(wave, Wave):
                wave.data = np.roll(wave.data, amount, axis=a)
            else:
                wave.data = roll(wave.data, amount, axis=a)
        return wave

    def getParams(self):
        return self.amount, self.axes


class ReflectFilter(FilterInterface):
    def __init__(self, type, axes):
        self.axes = axes
        self.type = type

    def _execute(self, wave, **kwargs):
        if isinstance(wave, Wave):
            lib = np
        elif isinstance(wave, DaskWave):
            lib = da
        for a in self.axes:
            sl = [slice(None)] * wave.data.ndim
            sl[a] = slice(None, None, -1)
            if self.type == "center":
                wave.data = wave.data + wave.data[tuple(sl)]
            if self.type == "first":
                wave.data = lib.concatenate([wave.data[tuple(sl)], wave.data], axis=a)
                wave.axes[a] = self._elongateAxis(wave.axes[a], self.type)
            if self.type == "last":
                wave.data = lib.concatenate([wave.data, wave.data[tuple(sl)]], axis=a)
                wave.axes[a] = self._elongateAxis(wave.axes[a], self.type)
        return wave

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

    def getParams(self):
        return self.type, self.axes
