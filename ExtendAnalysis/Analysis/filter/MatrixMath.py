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
