from ..filter.Convolution import *
from ..filter.Differentiate import *
from ..filtersGUI import *
from .CommonWidgets import *


class DifferentialSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Gradient': GradientSetting,
            'Nabla': NablaSetting,
            'Laplacian': LaplacianSetting,
            'Prewitt': PrewittSetting,
            'Sobel': SobelSetting,
            'Laplacian by Convolution': LaplacianConvSetting,
        }
        return d


class GradientSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self._layout = AxisCheckLayout(dim)
        self.setLayout(self._layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, GradientFilter):
            return True

    def GetFilter(self):
        return GradientFilter(self._layout.GetChecked())

    def parseFromFilter(self, f):
        obj = GradientSetting(None, self.dim, self.loader)
        axes = f.getAxes()
        obj._layout.SetChecked(axes)
        return obj


class NablaSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, NablaFilter):
            return True

    def GetFilter(self):
        return NablaFilter()

    def parseFromFilter(self, f):
        obj = NablaSetting(None, self.dim, self.loader)
        return obj


class LaplacianSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, LaplacianFilter):
            return True

    def GetFilter(self):
        return LaplacianFilter()

    def parseFromFilter(self, f):
        obj = LaplacianSetting(None, self.dim, self.loader)
        return obj


class PrewittSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self._layout = AxisCheckLayout(dim)
        self.setLayout(self._layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, PrewittFilter):
            return True

    def GetFilter(self):
        return PrewittFilter(self._layout.GetChecked())

    def parseFromFilter(self, f):
        obj = PrewittSetting(None, self.dim, self.loader)
        axes = f.getAxes()
        obj._layout.SetChecked(axes)
        return obj


class SobelSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self._layout = AxisCheckLayout(dim)
        self.setLayout(self._layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SobelFilter):
            return True

    def GetFilter(self):
        return SobelFilter(self._layout.GetChecked())

    def parseFromFilter(self, f):
        obj = SobelSetting(None, self.dim, self.loader)
        axes = f.getAxes()
        obj._layout.SetChecked(axes)
        return obj


class LaplacianConvSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self._layout = AxisCheckLayout(dim)
        self.setLayout(self._layout)

    @classmethod
    def _havingFilter(cls, f):
        if type(f) == LaplacianConvFilter:
            return True

    def GetFilter(self):
        return LaplacianConvFilter(self._layout.GetChecked())

    def parseFromFilter(self, f):
        obj = LaplacianConvSetting(None, self.dim, self.loader)
        axes = f.getAxes()
        obj._layout.SetChecked(axes)
        return obj


filterGroups['Differential Filter'] = DifferentialSetting
