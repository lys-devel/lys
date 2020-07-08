from ..filter.Region import *
from ..filtersGUI import *
from .CommonWidgets import *
from ExtendAnalysis import ScientificSpinBox


class IntegrationSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Axis': IntegralSetting,
        }
        return d


class IntegralSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self.__parent = parent
        self.range = RegionSelectWidget(self, dim, loader)
        self.setLayout(self.range)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, IntegralFilter):
            return True

    def GetFilter(self):
        return IntegralFilter(self.range.getRegion())

    def parseFromFilter(self, f):
        obj = IntegralSetting(None, self.dim, self.loader)
        region = f.getRegion()
        for i, r in enumerate(region):
            obj.range.setRegion(i, r)
        return obj


filterGroups['Integral'] = IntegrationSetting
