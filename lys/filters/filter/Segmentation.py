import numpy as np
import dask.array as da
from scipy.signal import medfilt
from scipy.ndimage import gaussian_filter

from lys import DaskWave
from .FilterInterface import FilterInterface


class ThresholdFilter(FilterInterface):
    """
    Segmentation by thresholding.

    If data >= *threshold*, the result is one. Otherwise, result is np.nan.

    If output = 'MaskedData', then this filter returns mask*data.

    If 'inv' is included in *output*, the mask is reverted.

    Args:
        threshold(float): value of threshold
        output('Mask', or 'MaskedData', or 'Mask_inv' or 'MaskedData_inv'): 'inv' means the mask is reverted.
    """

    def __init__(self, threshold, output="Mask"):
        self._threshold = threshold
        self._output = output

    def _execute(self, wave, *args, **kwargs):
        mask = wave.data.copy()
        if "inv" in self._output:
            mask[wave.data < self._threshold] = 1
            mask[wave.data >= self._threshold] = np.nan
        else:
            mask[wave.data < self._threshold] = np.nan
            mask[wave.data >= self._threshold] = 1
        if "Data" in self._output:
            result = wave.data * mask
        else:
            result = mask
        return DaskWave(result, *wave.axes, **wave.note)

    def getParameters(self):
        return {"threshold": self._threshold, "output": self._output}


class AdaptiveThresholdFilter(FilterInterface):
    """
    Segmentation by adaptive thresholding.

    When mode='Median', and if data >= median(data, size)+c, the result is one. Otherwise, result is np.nan.

    *axes* specifies which axes are used for thresholding. Median (and Gaussian) filter is applied along these axes.
    For 2-dimensional image, *axes*=(0,1) is used. If data.ndim != 2, users should specifies *axes* manually.

    If output = 'MaskedData', then this filter returns mask*data.
    If 'inv' is included in *output*, the mask is reverted.

    Args:
        size(int or float): size of Median and Gaussian filter in pixel units.
        c(float): offset for thresholding.
        mode('Median' or 'Gaussian'): specifies whether Median or Gaussian is applied to original data to generate adaptive threshold.
        output('Mask', or 'MaskedData', or 'Mask_inv' or 'MaskedData_inv'): see description above.
        axes(tuple of int): specifies axes used for adaptive thresholding.
    """

    def __init__(self, size, c, mode='Median', output='Mask', axes=(0, 1)):
        self._size = size
        self._c = c
        self._method = mode
        self._output = output
        self._axes = axes

    def _execute(self, wave, *args, **kwargs):
        def f(x): return _applyMask(x, self._method, self._output, self._size, self._c)
        sig = "("
        for i in range(len(self._axes)):
            sig += "ijklmnopqrst"[i] + ","
        sig = sig[:-1] + ")"
        gumap = da.gufunc(f, signature=sig + "->" + sig, output_dtypes=float, vectorize=True, axes=[tuple(self._axes), tuple(self._axes)], allow_rechunk=True)
        return DaskWave(gumap(wave.data), *wave.axes, **wave.note)

    def getParameters(self):
        return {"size": self._size, "c": self._c, "mode": self._method, "output": self._output, "axes": self._axes}


def _applyFilter(data, size, method):
    if method == 'Median':
        return medfilt(data, kernel_size=size)
    else:
        return gaussian_filter(data, sigma=size)


def _applyMask(data, method, output, size, c):
    fil = _applyFilter(data, size, method) + c
    if "inv" in output:
        mask = np.where(data >= fil, np.nan, 1)
    else:
        mask = np.where(data >= fil, 1, np.nan)
    if 'data' in output or 'Data' in output:
        data = data * mask
    else:
        data = mask
    return data
