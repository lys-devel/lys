from ..filter.Region import *
from ..filtersGUI import *
from .CommonWidgets import *
from lys import ScientificSpinBox


class NormalizationSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Reference': ReferenceNormalizeSetting,
            'Area': NormalizeSetting,
        }
        return d


class ReferenceNormalizeSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None, init=0):
        super().__init__(parent, dim, loader)
        self.__parent = parent
        self.__axis = AxisSelectionLayout("Axis", dim, init)
        self.__type = QComboBox()
        self.__type.addItems(["Diff", "Divide"])
        self.__ref = QComboBox()
        self.__ref.addItems(["First", "Last"])
        hbox = QHBoxLayout()
        hbox.addLayout(self.__axis)
        hbox.addWidget(self.__type)
        hbox.addWidget(self.__ref)
        self.setLayout(hbox)

    def GetFilter(self):
        ref = self.__ref.currentText()
        if ref == "First":
            ref = 0
        else:
            ref = -1
        return ReferenceNormalizeFilter(self.__axis.getAxis(), self.__type.currentText(), ref)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, ReferenceNormalizeFilter):
            return True

    def parseFromFilter(self, f):
        axis, type, ref = f.getParams()
        obj = ReferenceNormalizeSetting(None, self.dim, self.loader, init=axis)
        if type == "Diff":
            obj.__type.setCurrentIndex(0)
        else:
            obj.__type.setCurrentIndex(1)
        if ref == 0:
            obj.__ref.setCurrentIndex(0)
        else:
            obj.__ref.setCurrentIndex(1)
        return obj


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


class MaskSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self.__parent = parent
        self.__filename = QLineEdit()

        hbox = QHBoxLayout()
        hbox.addWidget(self.__filename)
        hbox.addWidget(QPushButton("Load", clicked=self._LoadMask))
        self.setLayout(hbox)

    def _LoadMask(self):
        file, _ = QFileDialog.getOpenFileName(
            None, 'Open file', filter="npz(*.npz)")
        if 0 != len(file):
            self.__filename.setText(file)

    def GetFilter(self):
        return MaskFilter(self.__filename.text())

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, MaskFilter):
            return True

    def parseFromFilter(self, f):
        filename = f.getParams()
        obj = MaskSetting(None, self.dim, self.loader)
        obj.__filename.setText(filename)

        return obj


class RefShiftSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self.__parent = parent
        self.range = RegionSelectWidget(self, dim, loader)
        self.combo = QComboBox()
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
        return ReferenceShiftFilter(self.combo.currentIndex(), self.range.getRegion())

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, ReferenceShiftFilter):
            return True

    def parseFromFilter(self, f):
        obj = RefShiftSetting(None, self.dim, self.loader)
        axis, region = f.getParams()
        obj.combo.setCurrentIndex(axis)
        for i, r in enumerate(region):
            obj.range.setRegion(i, r)
        return obj


filterGroups['Select region'] = SelectRegionSetting
filterGroups['Normalization'] = NormalizationSetting
filterGroups['Masking'] = MaskSetting
filterGroups['RefShift'] = RefShiftSetting
