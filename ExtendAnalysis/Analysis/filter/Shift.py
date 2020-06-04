import scipy
import numpy as np
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
            wave.data = (scipy.ndimage.interpolation.shift(np.array(wave.data, dtype=np.float32), self._s[0:wave.data.ndim], order=order, cval=0))
        else:
            wave.data = (scipy.ndimage.interpolation.shift(np.array(wave.data, dtype=np.float32), shift[0:wave.data.ndim], order=order, cval=0))


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
