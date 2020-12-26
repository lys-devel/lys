import numpy as np
import dask.array as da
from ExtendAnalysis import Wave, DaskWave
from .FilterInterface import FilterInterface


class SelectIndexFilter(FilterInterface):
    def __init__(self, axis, index):
        self._axis = axis
        self._index = index

    def _execute(self, wave, **kwargs):
        axes = list(wave.axes)
        axes.pop(self._axis)
        sl = [slice(None)] * wave.data.ndim
        sl[self._axis] = self._index
        wave.data = wave.data[tuple(sl)]
        wave.axes = axes
        return wave

    def getParams(self):
        return self._axis, self._index

    def getRelativeDimension(self):
        return -1


class IndexMathFilter(FilterInterface):
    def __init__(self, axis, type, index1, index2):
        self._type = type
        self._axis = axis
        self._index1 = index1
        self._index2 = index2

    def _execute(self, wave, **kwargs):
        axes = list(wave.axes)
        axes.pop(self._axis)
        sl1 = [slice(None)] * wave.data.ndim
        sl1[self._axis] = self._index1
        sl2 = [slice(None)] * wave.data.ndim
        sl2[self._axis] = self._index2
        if self._type == "+":
            wave.data = wave.data[tuple(sl1)] + wave.data[tuple(sl2)]
        if self._type == "-":
            wave.data = wave.data[tuple(sl1)] - wave.data[tuple(sl2)]
        if self._type == "*":
            wave.data = wave.data[tuple(sl1)] * wave.data[tuple(sl2)]
        if self._type == "/":
            wave.data = wave.data[tuple(sl1)] / wave.data[tuple(sl2)]
        wave.axes = axes
        return wave

    def getParams(self):
        return self._axis, self._type, self._index1, self._index2

    def getRelativeDimension(self):
        return -1


class TransposeFilter(FilterInterface):
    def __init__(self, axes):
        self._axes = axes

    def _execute(self, wave, **kwargs):
        wave.data = wave.data.transpose(self._axes)
        wave.axes = [wave.axes[i] for i in self._axes]
        return wave

    def getParams(self):
        return self._axes


class SliceFilter(FilterInterface):
    def __init__(self, slices):
        self._sl = slices

    def _execute(self, wave, **kwargs):
        slices = []
        for s in self._sl:
            if isinstance(s, int):
                slices.append(slice(s, s, 1))
            else:
                slices.append(slice(*s))
        axes = []
        for i, s in enumerate(slices):
            if (not s.start == s.stop) or (s.start is None):
                if wave.axisIsValid(i):
                    axes.append(wave.axes[i][s])
                else:
                    axes.append(None)
        for i, s in enumerate(slices):
            if s.start == s.stop and s.start is not None:
                slices[i] = s.start
        wave.data = wave.data[tuple(slices)]
        wave.axes = axes

    def getParams(self):
        return self._sl

    def getRelativeDimension(self):
        return -np.sum([1 for s in self._sl if s[0] == s[1]])
