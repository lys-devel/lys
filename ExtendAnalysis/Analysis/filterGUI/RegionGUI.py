from ..filter.Region import *
from ..filtersGUI import *
from .CommonWidgets import *
from ExtendAnalysis import ScientificSpinBox


class NormalizeSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self.__parent = parent
        self.range = RegionSelectWidget(self, dim, loader)
        self.combo = QComboBox()
        self.combo.addItem("Whole")
        for d in range(dim):
            self.combo.addItem("Axis" + str(d + 1))

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel("Axis"))
        vbox.addWidget(self.combo)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addLayout(self.range)
        self.setLayout(hbox)

    def GetFilter(self):
        return NormalizeFilter(self.range.getRegion(), self.combo.currentIndex() - 1)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, NormalizeFilter):
            return True

    def parseFromFilter(self, f):
        obj = NormalizeSetting(None, self.dim, self.loader)
        region, axis = f.getParams()
        obj.combo.setCurrentIndex(axis + 1)
        for i, r in enumerate(region):
            obj.range.setRegion(i, r)
        return obj


class SelectRegionSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self.__parent = parent
        self.range = RegionSelectWidget(self, dim, loader)
        self.setLayout(self.range)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SelectRegionFilter):
            return True

    def GetFilter(self):
        return SelectRegionFilter(self.range.getRegion())

    def parseFromFilter(self, f):
        obj = SelectRegionSetting(None, self.dim, self.loader)
        region = f.getRegion()
        for i, r in enumerate(region):
            obj.range.setRegion(i, r)
        return obj


filterGroups['Select region'] = SelectRegionSetting
filterGroups['Normalization'] = NormalizeSetting
