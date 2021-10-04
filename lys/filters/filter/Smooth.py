from dask_image import ndfilters

from lys import DaskWave
from .FilterInterface import FilterInterface


class MedianFilter(FilterInterface):
    """
    Apply median filter (scipy.ndimage.median_filter) to data.

    Args:
        kernel(list of int): kernel size along each axis.
    """

    def __init__(self, kernel):
        self._kernel = kernel

    def _execute(self, wave, *args, **kwargs):
        data = self._applyFunc(ndfilters.median_filter, wave.data, size=self._kernel)
        return DaskWave(data, *wave.axes, **wave.note)

    def getParameters(self):
        return {"kernel": self._kernel}


class AverageFilter(FilterInterface):
    """
    Apply average filter (scipy.ndimage.uniform_filter) to data.

    Args:
        kernel(list of int): kernel size along each axis.
    """

    def __init__(self, kernel):
        self._kernel = kernel

    def _execute(self, wave, *args, **kwargs):
        data = self._applyFunc(ndfilters.uniform_filter, wave.data.astype(float), size=self._kernel)
        return DaskWave(data, *wave.axes, **wave.note)

    def getParameters(self):
        return {"kernel": self._kernel}


class GaussianFilter(FilterInterface):
    """
    Apply gaussian filter (scipy.ndimage.gaussian_filter) to data.

    Args:
        kernel(list of int): kernel size (=sigma) along each axis.
    """

    def __init__(self, kernel):
        self._kernel = kernel

    def _execute(self, wave, *args, **kwargs):
        data = self._applyFunc(ndfilters.gaussian_filter, wave.data, sigma=self._kernel)
        return DaskWave(data, *wave.axes, **wave.note)

    def getParameters(self):
        return {"kernel": self._kernel}
