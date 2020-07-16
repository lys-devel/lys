import numpy as np
import dask.array as da

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
            letters = ["a", "b", "c", "d", "e", "f",
                       "g", "h", "i", "j", "k", "l", "m", "n"]
            axes.remove(self._axis)
            nor = 1 / wave.data[self._makeSlice(wave)].mean(axis=axes)
            subscripts = ""
            for i in range(wave.data.ndim):
                subscripts += letters[i]
            subscripts = subscripts + "," + \
                letters[self._axis] + "->" + subscripts
            if isinstance(wave, DaskWave):
                lib = da
            else:
                lib = np
            wave.data = lib.einsum(subscripts, wave.data, nor)

    def getParams(self):
        return self._range, self._axis


class ReferenceNormalizeFilter(FilterInterface):
    def __init__(self, axis, type, ref):
        self._type = type
        self._axis = axis
        self._ref = ref

    def _execute(self, wave, **kwargs):
        ref = self.__makeReference(wave)
        if self._type == "Diff":
            wave.data = wave.data - ref
        if self._type == "Divide":
            wave.data = wave.data / ref
        return wave

    def __makeReference(self, wave):
        if isinstance(wave, DaskWave):
            lib = da
        else:
            lib = np
        sl = [slice(None)] * wave.data.ndim
        sl[self._axis] = self._ref
        order = list(range(1, wave.data.ndim))
        order.insert(self._axis, 0)
        res = lib.stack([wave.data[tuple(sl)]] *
                        wave.data.shape[self._axis]).transpose(*order)
        return res

    def getParams(self):
        return self._axis, self._type, self._ref


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


class MaskFilter(FilterInterface):

    def __init__(self, filename):
        self._mask = filename

    def _execute(self, wave, **kwargs):
        mask = Wave(self._mask)
        if isinstance(wave, DaskWave):
            mask = DaskWave(mask)
        wave.data = wave.data*mask.data

    def getParams(self):
        return self._mask
