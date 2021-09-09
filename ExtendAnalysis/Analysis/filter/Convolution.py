import numpy as np
import dask.array as da
from dask_image import ndfilters as dfilters
from scipy.ndimage import filters

from .FilterInterface import FilterInterface


class GradientFilter(FilterInterface):
    def __init__(self, axes):
        self._axes = axes

    def _execute(self, wave, **kwargs):
        def f(d, x):
            if len(d) == 1:
                return x
            return np.gradient(d, x)
        for ax in self._axes:
            wave.data = da.apply_along_axis(f, ax, wave.data, wave.getAxis(ax))
        return wave

    def getAxes(self):
        return self._axes


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
            wave.data = self._applyFunc(dfilters.convolve, wave.data, kernel)
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
        wave.data = dfilters.convolve(wave.data, kernel)
        return wave


class SharpenFilter(LaplacianFilter):
    def _getKernel(self, core, axis):
        res = super()._getKernel(core, axis)
        res[tuple([1 for i in range(core.ndim)])] -= 1
        return res
