from ..filter.SimpleMath import *
from ..filtersGUI import *
from .CommonWidgets import *
from ExtendAnalysis import ScientificSpinBox


class SimpleMathSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Add': AddSetting,
            'Subtract': SubtractSetting,
            'Multiply': MultSetting,
            'Devide': DevideSetting,
            'Pow': PowSetting,
            'Complex': ComplexSetting,
            'Phase': PhaseSetting,
            'Replace nan': NanToNumSetting,
        }
        return d


class SimpleMathSettingBase(FilterSettingBase):
    def __init__(self, parent, dim, loader=None, type=""):
        super().__init__(parent, dim, loader)
        self._layout = QHBoxLayout()
        self._val1 = ScientificSpinBox()
        self._val2 = ScientificSpinBox()
        self._layout.addWidget(self._val1)
        self._layout.addWidget(QLabel('+'))
        self._layout.addWidget(self._val2)
        self._layout.addWidget(QLabel('i'))
        self._type = type
        self.setLayout(self._layout)

    def GetFilter(self):
        if self._val2.value() == 0:
            return SimpleMathFilter(self._type, self._val1.value())
        else:
            return SimpleMathFilter(self._type, self._val1.value() + self._val2.value() * 1j)


class AddSetting(SimpleMathSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader, "+")

    def parseFromFilter(self, f):
        obj = AddSetting(None, self.dim, self.loader)
        obj._val1.setValue(np.real(f._value))
        obj._val2.setValue(np.imag(f._value))
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
        obj._val1.setValue(np.real(f._value))
        obj._val2.setValue(np.imag(f._value))
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
        obj._val1.setValue(np.real(f._value))
        obj._val2.setValue(np.imag(f._value))
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
        obj._val1.setValue(np.real(f._value))
        obj._val2.setValue(np.imag(f._value))
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
        obj._val1.setValue(np.real(f._value))
        obj._val2.setValue(np.imag(f._value))
        return obj

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SimpleMathFilter):
            if f._type == '**':
                return True


class ComplexSetting(FilterSettingBase):
    types = ["absolute", "real", "imag"]

    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        layout = QHBoxLayout()
        self._combo = QComboBox()
        self._combo.addItems(self.types)
        layout.addWidget(self._combo)
        self.setLayout(layout)

    def GetFilter(self):
        return ComplexFilter(self._combo.currentText())

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, ComplexFilter):
            return True

    def parseFromFilter(self, f):
        obj = ComplexSetting(None, self.dim, self.loader)
        obj._combo.setCurrentIndex(self.types.index(f._type))
        return obj


class PhaseSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        layout = QHBoxLayout()
        self._phase = ScientificSpinBox()
        layout.addWidget(self._phase)
        layout.addWidget(QLabel("deg"))
        self.setLayout(layout)

    def GetFilter(self):
        r = self._phase.value()
        return PhaseFilter(r)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, PhaseFilter):
            return True

    def parseFromFilter(self, f):
        obj = PhaseSetting(None, self.dim, self.loader)
        val = f.getValue()
        self._phase.setValue(val)
        return obj


class NanToNumSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        layout = QHBoxLayout()
        self._real = ScientificSpinBox()
        self._imag = ScientificSpinBox()
        layout.addWidget(self._real)
        layout.addWidget(QLabel("+"))
        layout.addWidget(self._imag)
        layout.addWidget(QLabel("i"))
        self.setLayout(layout)

    def GetFilter(self):
        r = self._real.value()
        i = self._imag.value()
        if i != 0:
            val = r + i * 1j
        else:
            val = r
        return NanToNumFilter(r)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, NanToNumFilter):
            return True

    def parseFromFilter(self, f):
        obj = NanToNumSetting(None, self.dim, self.loader)
        val = f.getValue()
        self._real.setValue(np.real(val))
        self._imag.setValue(np.imag(val))
        return obj


filterGroups['Simple Math'] = SimpleMathSetting
