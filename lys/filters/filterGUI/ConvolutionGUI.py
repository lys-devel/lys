
from lys import filters
from ..filtersGUI import filterGroups, FilterGroupSetting, FilterSettingBase, filterGUI
from .CommonWidgets import AxisCheckLayout


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


class _AxisCheckSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self._layout = AxisCheckLayout(dim)
        self.setLayout(self._layout)

    def setParameters(self, axes):
        self._layout.SetChecked(axes)

    def getParameters(self):
        return {"axes": self._layout.GetChecked()}


@filterGUI(filters.GradientFilter)
class GradientSetting(_AxisCheckSetting):
    pass


@filterGUI(filters.NablaFilter)
class NablaSetting(FilterSettingBase):
    def setParameters(self):
        pass

    def getParameters(self):
        return {}


@filterGUI(filters.LaplacianFilter)
class LaplacianSetting(FilterSettingBase):
    def setParameters(self):
        pass

    def getParameters(self):
        return {}


@filterGUI(filters.PrewittFilter)
class PrewittSetting(_AxisCheckSetting):
    pass


@filterGUI(filters.SobelFilter)
class SobelSetting(_AxisCheckSetting):
    pass


@filterGUI(filters.LaplacianConvFilter)
class LaplacianConvSetting(_AxisCheckSetting):
    pass


filterGroups['Differential Filter'] = DifferentialSetting
