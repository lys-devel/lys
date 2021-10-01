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
            'Symmetrize': SymmetrizeSetting,
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


class SymmetrizeSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        layout = QHBoxLayout()
        self.axes = [AxisSelectionLayout(
            "Axis1", dim=dim, init=0), AxisSelectionLayout("Axis2", dim=dim, init=1)]
        self._combo = QComboBox()
        self._combo.addItem("1")
        self._combo.addItem("2")
        self._combo.addItem("3")
        self._combo.addItem("4")
        self._combo.addItem("6")
        layout.addWidget(self._combo)
        l0 = QGridLayout()
        self._center = [ScientificSpinBox(), ScientificSpinBox()]
        l0.addWidget(QLabel("Center1"), 0, 0)
        l0.addWidget(self._center[0], 1, 0)
        l0.addWidget(QLabel("Center2"), 0, 1)
        l0.addWidget(self._center[1], 1, 1)
        layout.addLayout(l0)
        lv = QVBoxLayout()
        lv.addLayout(self.axes[0])
        lv.addLayout(self.axes[1])
        lv.addLayout(layout)
        self.setLayout(lv)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SymmetrizeFilter):
            return True

    def GetFilter(self):
        axes = [c.getAxis() for c in self.axes]
        return SymmetrizeFilter(self._combo.currentText(), [i.value() for i in self._center], axes)

    def parseFromFilter(self, f):
        obj = SymmetrizeSetting(None, self.dim, self.loader)
        rot, center, axes = f.getParams()
        obj._center[0].setValue(center[0])
        obj._center[1].setValue(center[1])
        obj._combo.setCurrentText(rot)
        for c, i in zip(obj.axes, axes):
            c.setAxis(i)
        return obj


filterGroups['Symmetric Operations'] = SymmetricOperationSetting
