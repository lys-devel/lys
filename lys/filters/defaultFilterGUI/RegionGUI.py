from lys import filters
from ..filtersGUI import filterGroups, FilterGroupSetting, FilterSettingBase, filterGUI
from .CommonWidgets import *


class NormalizationSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Reference': ReferenceNormalizeSetting,
            'Area': NormalizeSetting,
        }
        return d


@filterGUI(filters.ReferenceNormalizeFilter)
class ReferenceNormalizeSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self.__axis = AxisSelectionLayout("Axis", dim)
        self.__type = QComboBox()
        self.__type.addItems(["Diff", "Divide"])
        self.__ref = QComboBox()
        self.__ref.addItems(["First", "Last"])
        hbox = QHBoxLayout()
        hbox.addLayout(self.__axis)
        hbox.addWidget(self.__type)
        hbox.addWidget(self.__ref)
        self.setLayout(hbox)

    def getParameters(self):
        ref = self.__ref.currentText()
        if ref == "First":
            ref = 0
        else:
            ref = -1
        return {"axis": self.__axis.getAxis(), "type": self.__type.currentText(), "refIndex": ref}

    def setParameters(self, axis, type, refIndex):
        self.__axis.setAxis(axis)
        if type == "Diff":
            self.__type.setCurrentIndex(0)
        else:
            self.__type.setCurrentIndex(1)
        if refIndex == 0:
            self.__ref.setCurrentIndex(0)
        else:
            self.__ref.setCurrentIndex(1)


@filterGUI(filters.NormalizeFilter)
class NormalizeSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self.range = RegionSelectWidget(self, dim)
        self.combo = QComboBox()
        self.combo.addItem("Whole")
        for d in range(dim):
            self.combo.addItem("Axis" + str(d + 1))

        vbox = QHBoxLayout()
        vbox.addWidget(QLabel("Normalization direction"))
        vbox.addWidget(self.combo)

        hbox = QVBoxLayout()
        hbox.addLayout(vbox)
        hbox.addLayout(self.range)
        self.setLayout(hbox)

    def getParameters(self):
        return {"range": self.range.getRegion(), "axis": self.combo.currentIndex() - 1}

    def setParameters(self, range, axis):
        self.combo.setCurrentIndex(axis + 1)
        for i, r in enumerate(range):
            self.range.setRegion(i, r)


@filterGUI(filters.SelectRegionFilter)
class SelectRegionSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self.range = RegionSelectWidget(self, dim)
        self.setLayout(self.range)

    def getParameters(self):
        return {"range": self.range.getRegion()}

    def setParameters(self, range):
        for i, r in enumerate(range):
            self.range.setRegion(i, r)


@filterGUI(filters.MaskFilter)
class MaskSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
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

    def getParameters(self):
        return {"filename": self.__filename.text()}

    def setParameters(self, filename):
        self.__filename.setText(filename)


@filterGUI(filters.ReferenceShiftFilter)
class RefShiftSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self.range = RegionSelectWidget(self, dim)
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

    def getParameters(self):
        return {"axis": self.combo.currentIndex(), "region": self.range.getRegion()}

    def setParameters(self, axis, region):
        self.combo.setCurrentIndex(axis)
        for i, r in enumerate(region):
            self.range.setRegion(i, r)


filterGroups['Select region'] = SelectRegionSetting
filterGroups['Normalization'] = NormalizationSetting
filterGroups['Masking'] = MaskSetting
filterGroups['RefShift'] = RefShiftSetting
