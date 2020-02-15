from ..filter.SimpleMath import *
from ..filtersGUI import *
from .CommonWidgets import *


class SimpleMathSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Add': AddSetting,
            'Subtract': SubtractSetting,
            'Multiply': MultSetting,
            'Devide': DevideSetting,
            'Pow': PowSetting,
        }
        return d


class SimpleMathSettingBase(FilterSettingBase):
    def __init__(self, parent, dim, loader=None, type=""):
        super().__init__(parent, dim, loader)
        self._layout = QHBoxLayout()
        self._val = QDoubleSpinBox()
        self._val.setDecimals(5)
        self._layout.addWidget(QLabel('Value'))
        self._layout.addWidget(self._val)
        self._type = type
        self.setLayout(self._layout)

    def GetFilter(self):
        return SimpleMathFilter(self._type, self._val.value())


class AddSetting(SimpleMathSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader, "+")

    def parseFromFilter(self, f):
        obj = AddSetting(None, self.dim, self.loader)
        obj._val.setValue(f._value)
        return obj

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SimpleMathFilter):
            if f._type == '+':
                return True


class SubtractSetting(SimpleMathSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader, "-")

    def parseFromFilter(self, f):
        obj = SubtractSetting(None, self.dim, self.loader)
        obj._val.setValue(f._value)
        return obj

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SimpleMathFilter):
            if f._type == '-':
                return True


class MultSetting(SimpleMathSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader, "*")

    def parseFromFilter(self, f):
        obj = MultSetting(None, self.dim, self.loader)
        obj._val.setValue(f._value)
        return obj

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SimpleMathFilter):
            if f._type == '*':
                return True


class DevideSetting(SimpleMathSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader, "/")

    def parseFromFilter(self, f):
        obj = DevideSetting(None, self.dim, self.loader)
        obj._val.setValue(f._value)
        return obj

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SimpleMathFilter):
            if f._type == '/':
                return True


class PowSetting(SimpleMathSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader, "**")

    def parseFromFilter(self, f):
        obj = PowSetting(None, self.dim, self.loader)
        obj._val.setValue(f._value)
        return obj

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SimpleMathFilter):
            if f._type == '**':
                return True


filterGroups['Simple Math'] = SimpleMathSetting
