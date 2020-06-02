import numpy as np

from ExtendAnalysis import Wave, DaskWave
from .FilterInterface import FilterInterface


class NormalizeFilter(FilterInterface):
    def _makeSlice(self, wave):
        sl = []
        for i, r in enumerate(self._range):
            if (r[0] == 0 and r[1] == 0) or self._axis == i:
                sl.append(slice(None))
            else:
                ind = wave.posToPoint(r, i)
                sl.append(slice(*ind))
        return tuple(sl)

    def __init__(self, range, axis):
        self._range = range
        self._axis = axis

    def _execute(self, wave, **kwargs):
        axes = list(range(wave.data.ndim))
        if self._axis == -1:
            wave.data = wave.data / wave.data[self._makeSlice(wave)].mean()
        else:
            letters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n"]
            axes.remove(self._axis)
            nor = 1 / wave.data[self._makeSlice()].mean(axis=axes)
            subscripts = ""
            for i in range(wave.data.ndim):
                subscripts += letters[i]
            subscripts = subscripts + "," + letters[self._axis] + "->" + subscripts
            wave.data = einsum(subscripts, wave.data, nor)

    def getParams(self):
        return self._range, self._axis


class SelectRegionFilter(FilterInterface):
    def __init__(self, range):
        self._range = np.array(range)

    def _execute(self, wave, **kwargs):
        sl = []
        for i, r in enumerate(self._range):
            if r[0] == 0 and r[1] == 0:
                sl.append(slice(None))
            else:
                ind = wave.posToPoint(r, i)
                sl.append(slice(*ind))
        key = tuple(sl)
        wave.data = wave.data[key]
        axes = []
        for s, ax in zip(key, wave.axes):
            if ax is None or (ax == np.array(None)).all():
                axes.append(None)
            else:
                axes.append(ax[s])
        wave.axes = axes
        return wave

    def getRegion(self):
        return self._range


class IntegralFilter(FilterInterface):
    def __init__(self, range):
        self._range = np.array(range)

    def _execute(self, wave, **kwargs):
        sl = []
        sumaxes = []
        for i, r in enumerate(self._range):
            if r[0] == 0 and r[1] == 0:
                sl.append(slice(None))
            else:
                ind = wave.posToPoint(r, i)
                sl.append(slice(*ind))
                sumaxes.append(i)
        key = tuple(sl)
        print(sumaxes, key)
        wave.data = np.sum(wave.data[key], axis=tuple(sumaxes))
        axes = []
        axis = 0
        for s, ax in zip(key, wave.axes):
            if not axis in sumaxes:
                if ax is None or (ax == np.array(None)).all():
                    axes.append(None)
                else:
                    axes.append(ax[s])
        wave.axes = axes
        return wave

    def getRegion(self):
        return self._range
