from ..filter.Interporation import *
from ..filter.Resize import *
from ..filtersGUI import *
from .CommonWidgets import *


class ResizeSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Interporation': InterpSetting,
            'Reduce size': ReduceSizeSetting,
            'Padding': PaddingSetting,
        }
        return d


class InterpSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self._vals = []
        self._layout = QGridLayout()
        for d in range(dim):
            self._layout.addWidget(QLabel("Axis" + str(d + 1)), 0, d)
            v = QSpinBox()
            v.setRange(0, 100000)
            self._vals.append(v)
            self._layout.addWidget(v, 1, d)
        self.setLayout(self._layout)

    def GetFilter(self):
        size = [v.value() for v in self._vals]
        return InterpFilter(size)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, InterpFilter):
            return True

    def parseFromFilter(self, f):
        obj = InterpSetting(None, self.dim, self.loader)
        for v, s in zip(obj._vals, f._size):
            v.setValue(s)
        return obj


class ReduceSizeSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._layout = kernelSizeLayout(dimension, odd=False)
        self.setLayout(self._layout)

    def GetFilter(self):
        return ReduceSizeFilter(self._layout.getKernelSize())

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, ReduceSizeFilter):
            return True

    def parseFromFilter(self, f):
        obj = ReduceSizeSetting(None, self.dim, self.loader)
        obj._layout.setKernelSize(f.getKernel())
        return obj


class PaddingSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._axes = AxisCheckLayout(dimension)
        self._size = QSpinBox()
        self._size.setRange(1, 100000)
        self._size.setValue(200)
        self._value = ScientificSpinBox()
        self._direction = QComboBox()
        self._direction.addItems(["first", "last", "both"])
        self._layout = QGridLayout()
        self._layout.addWidget(QLabel("axes"), 0, 0)
        self._layout.addWidget(QLabel("direction"), 0, 1)
        self._layout.addWidget(QLabel("size"), 0, 2)
        self._layout.addWidget(QLabel("value"), 0, 3)
        self._layout.addLayout(self._axes, 1, 0)
        self._layout.addWidget(self._direction, 1, 1)
        self._layout.addWidget(self._size, 1, 2)
        self._layout.addWidget(self._value, 1, 3)
        self.setLayout(self._layout)

    def GetFilter(self):
        return PaddingFilter(self._axes.GetChecked(), self._value.value(), self._size.value(), self._direction.currentText())

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, PaddingFilter):
            return True

    def parseFromFilter(self, f):
        obj = PaddingSetting(None, self.dim, self.loader)
        axes, value, size, direction = f.getParams()
        obj._axes.SetChecked(axes)
        obj._size.setValue(size)
        obj._value.setValue(value)
        if direction == "first":
            obj._direction.setCurrentIndex(0)
        else:
            obj._direction.setCurrentIndex(1)
        return obj


filterGroups["Resize and interporation"] = ResizeSetting
