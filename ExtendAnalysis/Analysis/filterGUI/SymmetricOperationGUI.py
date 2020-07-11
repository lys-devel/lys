from ..filter.Shift import *
from ..filtersGUI import *
from .CommonWidgets import *


class SymmetricOperationSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Reverse': ReverseSetting,
            'Roll': RollSetting,
            'Reflect': ReflectSetting,
        }
        return d


class ReverseSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self._axes = AxisCheckLayout(dim)
        self.setLayout(self._axes)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, ReverseFilter):
            return True

    def GetFilter(self):
        return ReverseFilter(self._axes.GetChecked())

    def parseFromFilter(self, f):
        obj = ReverseSetting(None, self.dim, self.loader)
        obj._axes.SetChecked(f.getAxes())
        return obj


class RollSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        layout = QHBoxLayout()
        self._combo = QComboBox()
        self._combo.addItem("1/2")
        self._combo.addItem("1/4")
        self._combo.addItem("-1/4")
        self._axes = AxisCheckLayout(dim)
        layout.addWidget(self._combo)
        layout.addLayout(self._axes)
        self.setLayout(layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, RollFilter):
            return True

    def GetFilter(self):
        return RollFilter(self._combo.currentText(), self._axes.GetChecked())

    def parseFromFilter(self, f):
        obj = RollSetting(None, self.dim, self.loader)
        type, axes = f.getParams()
        obj._axes.SetChecked(axes)
        obj._combo.setCurrentText(type)
        return obj


class ReflectSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        layout = QHBoxLayout()
        self._combo = QComboBox()
        self._combo.addItem("first")
        self._combo.addItem("last")
        self._combo.addItem("center")
        self._axes = AxisCheckLayout(dim)
        layout.addWidget(self._combo)
        layout.addLayout(self._axes)
        self.setLayout(layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, ReflectFilter):
            return True

    def GetFilter(self):
        return ReflectFilter(self._combo.currentText(), self._axes.GetChecked())

    def parseFromFilter(self, f):
        obj = ReflectSetting(None, self.dim, self.loader)
        type, axes = f.getParams()
        obj._axes.SetChecked(axes)
        obj._combo.setCurrentText(type)
        return obj


filterGroups['Symmetric Operations'] = SymmetricOperationSetting
