import numpy as np

from dask_image import ndfilters as dfilters
from scipy.ndimage import filters

from ExtendAnalysis import Wave, DaskWave
from .FilterInterface import FilterInterface


class _SmoothFilterBase(FilterInterface):
    def getFilterLib(self, wave):
        if isinstance(wave, DaskWave):
            return dfilters
        return filters


class MedianFilter(_SmoothFilterBase):
    def __init__(self, kernel):
        self._kernel = [int((k + 1) / 2) for k in kernel]

    def _execute(self, wave, **kwargs):
        f = self.getFilterLib(wave).median_filter
        wave.data = self._applyFunc(f, wave.data, size=self._kernel)
        return wave

    def getKernel(self):
        return [int(2 * k - 1) for k in self._kernel]


class AverageFilter(_SmoothFilterBase):
    def __init__(self, kernel):
        self._kernel = [int((k + 1) / 2) for k in kernel]

    def _execute(self, wave, **kwargs):
        f = self.getFilterLib(wave).uniform_filter
        wave.data = self._applyFunc(f, wave.data, size=self._kernel)
        return wave

    def getKernel(self):
        return [int(2 * k - 1) for k in self._kernel]


class GaussianFilter(_SmoothFilterBase):
    def __init__(self, kernel):
        self._kernel = kernel

    def _execute(self, wave, **kwargs):
        f = self.getFilterLib(wave).gaussian_filter
        wave.data = self._applyFunc(f, wave.data, sigma=self._kernel)
        return wave

    def getKernel(self):
        return self._kernel


class BilateralFilter(FilterInterface):
    def __init__(self, kernel, s_color, s_space):
        self._kernel = kernel
        self._sc = s_color
        self._ss = s_space

    def _execute(self, wave, **kwargs):
        wave.data = cv2.bilateralFilter(np.array(wave.data, dtype=np.float32), self._kernel, self._sc, self._ss)
