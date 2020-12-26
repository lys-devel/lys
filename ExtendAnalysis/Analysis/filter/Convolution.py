import numpy as np
from dask_image import ndfilters as dfilters
from scipy.ndimage import filters

from ExtendAnalysis import Wave, DaskWave
from .FilterInterface import FilterInterface


class ConvolutionFilter(FilterInterface):
    def __init__(self, axes):
        self._axes = axes

    def makeCore(self, dim):
        core = np.zeros([3 for i in range(dim)])
        core[tuple([1 for i in range(dim)])] = 1
        return core

    def _getKernel(self, core, axis):
        raise NotImplementedError()

    def _kernel(self, wave, axis):
        core = self.makeCore(self._getDim(wave))
        return self._getKernel(core, axis)

    def _getDim(self, wave):
        if isinstance(wave, np.ndarray):
            return wave.ndim
        else:
            return wave.data.ndim

    def _execute(self, wave, **kwargs):
        for ax in self._axes:
            kernel = self._kernel(wave, ax)
            if isinstance(wave, Wave):
                wave.data = self._applyFunc(filters.convolve, wave.data, kernel)
            if isinstance(wave, DaskWave):
                wave.data = self._applyFunc(dfilters.convolve, wave.data, kernel)
            else:
                wave = filters.convolve(wave, kernel)
        return wave

    def getAxes(self):
        return self._axes


class PrewittFilter(ConvolutionFilter):
    def _getKernel(self, core, axis):
        return filters.prewitt(core, axis=axis)


class SobelFilter(ConvolutionFilter):
    def _getKernel(self, core, axis):
        return filters.sobel(core, axis=axis)


class LaplacianFilter(ConvolutionFilter):
    def _getKernel(self, core, axis):
        res = np.array(core)
        for ax in self._axes:
            res += filters.convolve1d(core, [1, -2, 1], axis=ax)
        res[tuple([1 for i in range(core.ndim)])] -= 1
        return res

    def _execute(self, wave, **kwargs):
        kernel = self._kernel(wave, None)
        if isinstance(wave, Wave):
            wave.data = filters.convolve(wave.data, kernel)
        if isinstance(wave, DaskWave):
            wave.data = dfilters.convolve(wave.data, kernel)
        else:
            wave = filters.convolve(wave, kernel)
        return wave


class SharpenFilter(LaplacianFilter):
    def _getKernel(self, core, axis):
        res = super()._getKernel(core, axis)
        res[tuple([1 for i in range(core.ndim)])] -= 1
        return res
