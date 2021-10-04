from lys import filters
from ..filtersGUI import filterGroups, FilterGroupSetting, FilterSettingBase, filterGUI
from .CommonWidgets import *


class SmoothingSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Median': MedianSetting,
            'Average': AverageSetting,
            'Gaussian': GaussianSetting
        }
        return d


@filterGUI(filters.MedianFilter)
class MedianSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = kernelSizeLayout(dimension)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"kernel": self._layout.getKernelSize()}

    def setParameters(self, kernel):
        self._layout.setKernelSize(kernel)


@filterGUI(filters.AverageFilter)
class AverageSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = kernelSizeLayout(dimension)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"kernel": self._layout.getKernelSize()}

    def setParameters(self, kernel):
        self._layout.setKernelSize(kernel)


@filterGUI(filters.GaussianFilter)
class GaussianSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = kernelSigmaLayout(dimension)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"kernel": self._layout.getKernelSigma()}

    def setParameters(self, kernel):
        self._layout.setKernelSigma(kernel)


filterGroups['Smoothing Filter'] = SmoothingSetting
