import numpy as np
import dask.array as da
from dask_image import ndfilters as dfilters
from scipy.ndimage import filters

from lys import DaskWave
from lys.filters import FilterSettingBase, filterGUI, addFilter

from .FilterInterface import FilterInterface
from .Differentiate import _AxisCheckSetting
from .CommonWidgets import *


class _ConvolutionFilter(FilterInterface):
    def __init__(self, axes):
        if not hasattr(axes, "__iter__"):
            self._axes = [axes]
        else:
            self._axes = axes

    def _makeCore(self, dim):
        core = np.zeros([3 for i in range(dim)])
        core[tuple([1 for i in range(dim)])] = 1
        return core

    def _getKernel(self, core, axis):
        raise NotImplementedError()

    def _kernel(self, wave, axis):
        core = self._makeCore(wave.data.ndim)
        return self._getKernel(core, axis)

    def _getDim(self, wave):
        return wave.data.ndim

    def _execute(self, wave, *args, **kwargs):
        results = [self._applyFunc(dfilters.convolve, wave.data, self._kernel(wave, ax)) for ax in self._axes]
        data = da.sum(da.stack(results), axis=0)
        return DaskWave(data, *wave.axes, **wave.note)

    def getParameters(self):
        return {"axes": self._axes}


class PrewittFilter(_ConvolutionFilter):
    """
    Apply prewitt filter.

    Args:
        axes(tuple of int): axes of wave along which to apply.

    Example:

        >>> w = Wave([1, 2, 3, 4, 5])
        >>> f = filters.PrewittFilter(axes=[0])
        >>> result = f.execute(w)
        >>> result.data
        >>> # [1,2,2,2,1]

    """

    def _getKernel(self, core, axis):
        return filters.prewitt(core, axis=axis)


class SobelFilter(_ConvolutionFilter):
    """
    Apply prewitt filter.

    Args:
        axes(tuple of int): axes of wave along which to apply.

    Example:

        >>> w = Wave([1, 2, 3, 4, 5])
        >>> f = filters.SobelFilter(axes=[0])
        >>> result = f.execute(w)
        >>> result.data
        >>> # [1,2,2,2,1]

    """

    def _getKernel(self, core, axis):
        return filters.sobel(core, axis=axis)


class LaplacianConvFilter(_ConvolutionFilter):
    """
    Apply Laplacian by convolution.

    Args:
        axes(tuple of int): axes of wave along which to apply.

    Example:

        >>> w = Wave([1, 2, 3, 4, 5])
        >>> f = filters.LaplacianConvFilter(axes=[0])
        >>> result = f.execute(w)
        >>> result.data
        >>> # [1,0,0,0,-1]

    """

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


@filterGUI(PrewittFilter)
class _PrewittSetting(_AxisCheckSetting):
    pass


@filterGUI(SobelFilter)
class _SobelSetting(_AxisCheckSetting):
    pass


@filterGUI(LaplacianConvFilter)
class _LaplacianConvSetting(_AxisCheckSetting):
    pass


addFilter(PrewittFilter, gui=_PrewittSetting, guiName="Prewitt filter", guiGroup="Differentiate")
addFilter(SobelFilter, gui=_SobelSetting, guiName="Sobel filter", guiGroup="Differentiate")
addFilter(LaplacianConvFilter, gui=_LaplacianConvSetting, guiName="Laplacian by convolution", guiGroup="Differentiate")
