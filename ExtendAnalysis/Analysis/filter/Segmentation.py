import numpy as np
import dask.array as da
from scipy.signal import medfilt
from scipy.ndimage import gaussian_filter

from ExtendAnalysis import Wave, DaskWave
from .FilterInterface import FilterInterface


class AdaptiveThresholdFilter(FilterInterface):
    def __init__(self, size, c, mode='Median', output='Mask', axes=(0, 1)):
        self._size = size
        self._c = c
        self._method = mode
        self._output = output
        self._axes = axes

    def _execute(self, wave, **kwargs):
        def f(x): return _applyMask(x, self._method, self._output, self._size, self._c)
        gumap = da.gufunc(f, signature="(i,j)->(i,j)", output_dtypes=wave.data.dtype, vectorize=True, axes=[tuple(self._axes), tuple(self._axes)], allow_rechunk=True)
        wave.data = gumap(wave.data)
        return wave

    def getParams(self):
        return self._size, self._c, self._method, self._output, self._axes


def _applyFilter(data, size, method):
    if method == 'Median':
        return medfilt(data, kernel_size=size)
    else:
        return gaussian_filter(data, sigma=size)


def _applyMask(data, method, output, size, c):
    fil = _applyFilter(data, size, method)+c
    if "inv" in output:
        mask = np.where(fil-data > 0, np.nan, 1)
    else:
        mask = np.where(fil-data > 0, 1, np.nan)
    if 'data' in output:
        data = data*mask
    else:
        data = mask
    return data


class ThresholdFilter(FilterInterface):
    def __init__(self, threshold):
        self._threshold = threshold

    def _execute(self, wave, **kwargs):
        if isinstance(wave, Wave):
            wave.data = np.where(wave.data > self._threshold, 1, 0)
        if isinstance(wave, DaskWave):
            wave.data = wave.data.copy()
            wave.data[wave.data < self._threshold] = 0
            wave.data[wave.data >= self._threshold] = 1
        return wave

    def getParams(self):
        return self._threshold
