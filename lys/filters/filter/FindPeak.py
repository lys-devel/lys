import numpy as np
from scipy.signal import argrelextrema
from scipy.ndimage import median_filter

from lys import DaskWave
from .FilterInterface import FilterInterface


class PeakFilter(FilterInterface):
    def __init__(self, axis, order, type="ArgRelMax", size=1):
        self._order = order
        self._type = type
        self._axis = axis
        self._size = size

    def _execute(self, wave, *args, **kwargs):
        if self._type == "ArgRelMax":
            def f(x): return _relmax(x, self._order, self._size)
        else:
            def f(x): return _relmin(x, self._order, self._size)
        axes = [ax for ax in wave.axes]
        axes[self._axis] = None
        uf = self._generalizedFunction(wave, f, signature="(i)->(j)", axes=[(self._axis,), (self._axis)], output_dtypes=float, output_sizes={"j": self._size})
        return DaskWave(uf(wave.data), *axes, **wave.note)

    def getParams(self):
        return {"axis": self._axis, "order": self._order, "type": self._type, "size": self._size}


def _relmax(x, order, size):
    data = argrelextrema(x, np.greater_equal, order=order)[0]
    res = [d for d in data if d != 0 and d != len(x) - 1]
    while len(res) < size:
        res.append(0)
    return np.array(res[:size])


def _relmin(x, order, size):
    data = argrelextrema(x, np.less_equal, order=order)[0]
    res = [d for d in data if d != 0 and d != len(x) - 1]
    res = list(data)
    while len(res) < size:
        res.append(0)
    return np.array(res[:size])


class PeakPostFilter(FilterInterface):
    def __init__(self, axis, medSize):
        self._axis = axis
        self._size = medSize

    def _execute(self, wave, *args, **kwargs):
        uf = self._generalizedFunction(wave, _find4D, signature="(i,j,k,l),(m)->(i,j,k,l)", axes=[(0, 1, 2, 3), (0), (0, 1, 2, 3)])
        return DaskWave(uf(wave.data, np.array(self._size)), *wave.axes, **wave.note)

    def getParams(self):
        return {"axis": self._axis, "size": self._size}


def _find4D(data, medSize):
    edge = [_findNearest(data[0, :, :, 0], np.median(data[0, :, n, 0])) for n in range(data.shape[2])]
    plane = [_findNearest(data.transpose(1, 0, 2, 3)[:, :, :, 0], e, medSize[0]).transpose(1, 0) for e in edge]
    volume = [_findNearest(data.transpose(0, 1, 3, 2), p, medSize[1]) for p in plane]
    return np.array(volume).transpose(1, 2, 0, 3)


def _findNearest(data, reference, medSize=1):  # reference: n-dim array, data: (n+2)-dim array, return (n+1)-dim array
    ref = median_filter(np.array(reference), medSize)
    mesh = np.meshgrid(*[range(x) for x in ref.shape], indexing="ij")
    res = []
    for i in range(data.shape[-2]):
        sl = [slice(None)] * (data.ndim)
        sl[-2] = i
        tile = tuple([data.shape[-1]] + [1] * (data.ndim - 2))
        order = list(range(1, ref.ndim + 1)) + [0]
        diff = np.abs(data[tuple(sl)] - np.tile(ref, tile).transpose(*order))
        index = np.argmin(diff, axis=-1)
        sl2 = mesh + [i] + [index]
        ref = data[tuple(sl2)]
        res.append(ref)
        ref = median_filter(ref, medSize)
    return np.array(res).transpose(order)


class PeakReorderFilter(FilterInterface):
    def __init__(self, peakAxis, scanAxis, medSize):
        self._peak = peakAxis
        self._scan = scanAxis
        self._size = medSize

    def _execute(self, wave, *args, **kwargs):
        axes = list(range(len(wave.data.shape)))
        axes.remove(self._peak)
        axes.remove(self._scan)
        axes = [self._peak, self._scan] + axes
        def f(x): return _reorder(x, self._size)
        uf = self._generalizedFunction(wave, f, signature="(i,j,k,l)->(i,j,k,l)", axes=[axes, axes])
        return DaskWave(uf(wave.data), *wave.axes, **wave.note)

    def getParams(self):
        return {"peakAxis": self._peak, "scanAxis": self._scan, "medSize": self._size}


def _reorder(data, size):
    res = []
    for n in range(data.shape[0]):
        ref = data[n][0]
        mesh = np.meshgrid(*[range(x) for x in ref.shape], indexing="ij")
        tmp = [ref]
        for m in range(1, data.shape[1]):
            diff = np.abs(data[:, m] - median_filter(ref, size))
            index = np.argmin(diff, axis=0)
            ref = data[tuple([index, m, *mesh])]
            tmp.append(ref)
        res.append(np.array(tmp))
    return np.array(res)
