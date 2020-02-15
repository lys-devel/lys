import numpy as np

from dask_image import ndfilters as dfilters
from scipy.ndimage import filters

from ExtendAnalysis import Wave, DaskWave
from .FilterInterface import FilterInterface


class MedianFilter(FilterInterface):
    def __init__(self, kernel):
        self._kernel = [int((k + 1) / 2) for k in kernel]

    def _execute(self, wave, **kwargs):
        if isinstance(wave, Wave):
            wave.data = filters.median_filter(wave.data, size=self._kernel)
            return wave
        if isinstance(wave, DaskWave):
            wave.data = dfilters.median_filter(wave.data, size=self._kernel)
            return wave
        return filters.median_filter(wave, size=self._kernel)

    def getKernel(self):
        return [int(2 * k - 1) for k in self._kernel]


class AverageFilter(FilterInterface):
    def __init__(self, kernel):
        self._kernel = [int((k + 1) / 2) for k in kernel]

    def _execute(self, wave, **kwargs):
        if isinstance(wave, Wave):
            wave.data = filters.uniform_filter(wave.data, size=self._kernel)
            return wave
        if isinstance(wave, DaskWave):
            wave.data = dfilters.uniform_filter(wave.data, size=self._kernel)
            return wave
        return filters.uniform_filter(wave, size=self._kernel)

    def getKernel(self):
        return [int(2 * k - 1) for k in self._kernel]


class GaussianFilter(FilterInterface):
    def __init__(self, kernel):
        self._kernel = kernel

    def _execute(self, wave, **kwargs):
        if isinstance(wave, Wave):
            wave.data = filters.gaussian_filter(wave.data, sigma=self._kernel)
            return wave
        if isinstance(wave, DaskWave):
            wave.data = dfilters.gaussian_filter(wave.data, sigma=self._kernel)
            return wave
        return filters.gaussian_filter(wave, sigma=self._kernel)

    def getKernel(self):
        return self._kernel


class BilateralFilter(FilterInterface):
    def __init__(self, kernel, s_color, s_space):
        self._kernel = kernel
        self._sc = s_color
        self._ss = s_space

    def _execute(self, wave, **kwargs):
        wave.data = cv2.bilateralFilter(np.array(wave.data, dtype=np.float32), self._kernel, self._sc, self._ss)
