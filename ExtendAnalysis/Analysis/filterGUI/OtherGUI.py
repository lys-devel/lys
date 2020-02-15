from ..filter.Interporation import *
from ..filter.Resize import *
from ..filtersGUI import *
from .CommonWidgets import *


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


filterGroups['*Interpolation'] = InterpSetting
filterGroups['Reduce size'] = ReduceSizeSetting
