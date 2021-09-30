from ..filter.Smooth import *
from ..filtersGUI import *
from .CommonWidgets import *


class SmoothingSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Median': MedianSetting,
            'Average': AverageSetting,
            'Gaussian': GaussianSetting
            # 'Bilateral': BilateralSetting
        }
        return d


class MedianSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._layout = kernelSizeLayout(dimension)
        self.setLayout(self._layout)

    def GetFilter(self):
        return MedianFilter(self._layout.getKernelSize())

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, MedianFilter):
            return True

    def parseFromFilter(self, f):
        obj = MedianSetting(None, self.dim, self.loader)
        obj._layout.setKernelSize(f.getKernel())
        return obj


class AverageSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._layout = kernelSizeLayout(dimension)
        self.setLayout(self._layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, AverageFilter):
            return True

    def GetFilter(self):
        return AverageFilter(self._layout.getKernelSize())

    def parseFromFilter(self, f):
        obj = AverageSetting(None, self.dim, self.loader)
        obj._layout.setKernelSize(f.getKernel())
        return obj


class GaussianSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._layout = kernelSigmaLayout(dimension)
        self.setLayout(self._layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, GaussianFilter):
            return True

    def GetFilter(self):
        return GaussianFilter(self._layout.getKernelSigma())

    def parseFromFilter(self, f):
        obj = GaussianSetting(None, self.dim, self.loader)
        obj._layout.setKernelSigma(f.getKernel())
        return obj


class BilateralSetting(QWidget):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent)
        self._layout = QHBoxLayout()
        self._kernel = QSpinBox()
        self._kernel.setMinimum(3)
        self._kernel.setValue(5)
        self._s_color = QSpinBox()
        self._s_color.setMinimum(1)
        self._s_color.setValue(7)
        self._s_space = QSpinBox()
        self._s_space.setMinimum(1)
        self._s_space.setValue(7)
        self._layout.addWidget(QLabel('Kernel Size'))
        self._layout.addWidget(self._kernel)
        self._layout.addWidget(QLabel('Sigma color'))
        self._layout.addWidget(self._s_color)
        self._layout.addWidget(QLabel('Sigma space'))
        self._layout.addWidget(self._s_space)
        self.setLayout(self._layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, BilateralFilter):
            return True

    def GetFilter(self):
        return BilateralFilter(self._kernel.value(), self._s_color.value(), self._s_space.value())


filterGroups['Smoothing Filter'] = SmoothingSetting
