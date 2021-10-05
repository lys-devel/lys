from lys import filters
from ..filtersGUI import filterGroups, FilterGroupSetting, FilterSettingBase, filterGUI
from .CommonWidgets import *


class SymmetricOperationSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Reverse': ReverseSetting,
            'Roll': RollSetting,
            'Reflect': ReflectSetting,
            'Symmetrize': SymmetrizeSetting,
        }
        return d


@filterGUI(filters.ReverseFilter)
class ReverseSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self._axes = AxisCheckLayout(dim)
        self.setLayout(self._axes)

    def getParameters(self):
        return {"axes": self._axes.GetChecked()}

    def setParameters(self, axes):
        self._axes.SetChecked(axes)


@filterGUI(filters.RollFilter)
class RollSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        layout = QHBoxLayout()
        self._combo = QComboBox()
        self._combo.addItems(["1/2", "1/4", "-1/4"])
        self._axes = AxisCheckLayout(dim)
        layout.addWidget(self._combo)
        layout.addLayout(self._axes)
        self.setLayout(layout)

    def getParameters(self):
        return {"amount": self._combo.currentText(), "axes": self._axes.GetChecked()}

    def setParameters(self, amount, axes):
        self._axes.SetChecked(axes)
        self._combo.setCurrentText(amount)


@ filterGUI(filters.ReflectFilter)
class ReflectSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        layout = QHBoxLayout()
        self._combo = QComboBox()
        self._combo.addItem("first")
        self._combo.addItem("last")
        self._combo.addItem("center")
        self._axes = AxisCheckLayout(dim)
        layout.addWidget(self._combo)
        layout.addLayout(self._axes)
        self.setLayout(layout)

    def getParameters(self):
        return {"type": self._combo.currentText(), "axes": self._axes.GetChecked()}

    def setParameters(self, type, axes):
        self._axes.SetChecked(axes)
        self._combo.setCurrentText(type)


@ filterGUI(filters.SymmetrizeFilter)
class SymmetrizeSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        layout = QHBoxLayout()
        self.axes = [AxisSelectionLayout("Axis1", dim=dim, init=0), AxisSelectionLayout("Axis2", dim=dim, init=1)]
        self._combo = QComboBox()
        self._combo.addItems(["1", "2", "3", "4", "6"])
        l0 = QGridLayout()
        self._center = [ScientificSpinBox(), ScientificSpinBox()]
        l0.addWidget(QLabel("Symmetry (fold)"), 0, 0)
        l0.addWidget(self._combo, 1, 0)
        l0.addWidget(QLabel("Center1"), 0, 1)
        l0.addWidget(self._center[0], 1, 1)
        l0.addWidget(QLabel("Center2"), 0, 2)
        l0.addWidget(self._center[1], 1, 2)
        layout.addLayout(l0)
        lv = QVBoxLayout()
        lv.addLayout(self.axes[0])
        lv.addLayout(self.axes[1])
        lv.addLayout(layout)
        self.setLayout(lv)

    def getParameters(self):
        return {"rotation": self._combo.currentText(), "center": [i.value() for i in self._center], "axes": [c.getAxis() for c in self.axes]}

    def setParameters(self, rotation, center, axes):
        self._center[0].setValue(center[0])
        self._center[1].setValue(center[1])
        self._combo.setCurrentText(rotation)
        for c, i in zip(self.axes, axes):
            c.setAxis(i)


filterGroups['Symmetric Operations'] = SymmetricOperationSetting
