import numpy as np
from dask_image import ndfilters

from lys import DaskWave
from lys.filters import FilterSettingBase, filterGUI, addFilter

from .FilterInterface import FilterInterface
from .CommonWidgets import kernelSizeLayout, kernelSigmaLayout


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
        kernel = []
        for i in range(wave.data.ndim):
            ax = wave.getAxis(i)
            kernel.append(self._kernel[i]/abs(ax[1]-ax[0])/(2*np.sqrt(2*np.log(2))))
        data = self._applyFunc(ndfilters.gaussian_filter, wave.data, sigma=kernel)
        return DaskWave(data, *wave.axes, **wave.note)

    def getParameters(self):
        return {"kernel": self._kernel}


@filterGUI(MedianFilter)
class _MedianSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = kernelSizeLayout(dimension)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"kernel": self._layout.getKernelSize()}

    def setParameters(self, kernel):
        self._layout.setKernelSize(kernel)


@filterGUI(AverageFilter)
class _AverageSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = kernelSizeLayout(dimension)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"kernel": self._layout.getKernelSize()}

    def setParameters(self, kernel):
        self._layout.setKernelSize(kernel)


@filterGUI(GaussianFilter)
class _GaussianSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = kernelSigmaLayout(dimension)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"kernel": self._layout.getKernelSigma()}

    def setParameters(self, kernel):
        self._layout.setKernelSigma(kernel)


addFilter(MedianFilter, gui=_MedianSetting, guiName="Median", guiGroup="Smoothing")
addFilter(AverageFilter, gui=_AverageSetting, guiName="Average", guiGroup="Smoothing")
addFilter(GaussianFilter, gui=_GaussianSetting, guiName="Gaussian", guiGroup="Smoothing")
