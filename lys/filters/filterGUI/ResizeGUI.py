from lys import filters
from ..filtersGUI import filterGroups, FilterGroupSetting, FilterSettingBase, filterGUI
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


@filterGUI(filters.InterpFilter)
class InterpSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self._vals = []
        self._layout = QGridLayout()
        for d in range(dim):
            self._layout.addWidget(QLabel("Axis" + str(d + 1)), 0, d)
            v = QSpinBox()
            v.setRange(0, 100000)
            self._vals.append(v)
            self._layout.addWidget(v, 1, d)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"size": [v.value() for v in self._vals]}

    def setParameters(self, size):
        for v, s in zip(self._vals, size):
            v.setValue(s)


@filterGUI(filters.ReduceSizeFilter)
class ReduceSizeSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = kernelSizeLayout(dimension, odd=False)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"kernel": self._layout.getKernelSize()}

    def setParameters(self, kernel):
        self._layout.setKernelSize(kernel)


@filterGUI(filters.PaddingFilter)
class PaddingSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
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

    def getParameters(self):
        return {"axes": self._axes.GetChecked(), "value": self._value.value(), "size": self._size.value(), "position": self._direction.currentText()}

    def setParameters(self, axes, value, size, position):
        self._axes.SetChecked(axes)
        self._size.setValue(size)
        self._value.setValue(value)
        if position == "first":
            self._direction.setCurrentIndex(0)
        else:
            self._direction.setCurrentIndex(1)


filterGroups["Resize and interporation"] = ResizeSetting
