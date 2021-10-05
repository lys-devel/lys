from lys import filters
from ..filtersGUI import filterGroups, FilterGroupSetting, FilterSettingBase, filterGUI
from .CommonWidgets import *


class IntegrationSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Axis': IntegralAllSetting,
            'Range': IntegralSetting,
            'Circle': CircleSetting,
        }
        return d


@filterGUI(filters.IntegralAllFilter)
class IntegralAllSetting(FilterSettingBase):
    _sumtypes = ["Sum", "Mean", "Median", "Max", "Min"]

    def __init__(self, dim):
        super().__init__(dim)
        self.type = QComboBox()
        self.type.addItems(self._sumtypes)
        self.axes = AxisCheckLayout(dim)
        lv = QVBoxLayout()
        lv.addWidget(self.type)
        lv.addLayout(self.axes)
        self.setLayout(lv)

    def getParameters(self):
        return {"axes": self.axes.GetChecked(), "sumtype": self.type.currentText()}

    def setParameters(self, axes, sumtype):
        self.axes.SetChecked(axes)
        self.type.setCurrentIndex(self._sumtypes.index(sumtype))


@filterGUI(filters.IntegralFilter)
class IntegralSetting(FilterSettingBase):
    _sumtypes = ["Sum", "Mean", "Median", "Max", "Min"]

    def __init__(self, dim):
        super().__init__(dim)
        self.type = QComboBox()
        self.type.addItems(self._sumtypes)
        self.range = RegionSelectWidget(self, dim)
        lv = QVBoxLayout()
        lv.addWidget(self.type)
        lv.addLayout(self.range)
        self.setLayout(lv)

    def getParameters(self):
        return {"range": self.range.getRegion(), "sumtype": self.type.currentText()}

    def setParameters(self, range, sumtype):
        self.type.setCurrentIndex(self._sumtypes.index(sumtype))
        for i, r in enumerate(range):
            self.range.setRegion(i, r)


@filterGUI(filters.IntegralCircleFilter)
class CircleSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self.axes = [AxisSelectionLayout("Axis1", dim=dim, init=0), AxisSelectionLayout("Axis2", dim=dim, init=1)]
        self.center = [ScientificSpinBox(), ScientificSpinBox()]
        self.radiuses = [ScientificSpinBox(), ScientificSpinBox()]
        l0 = QGridLayout()
        l0.addWidget(QLabel("Center1"), 0, 0)
        l0.addWidget(self.center[0], 1, 0)
        l0.addWidget(QLabel("Center2"), 0, 1)
        l0.addWidget(self.center[1], 1, 1)
        l0.addWidget(QLabel("R"), 0, 2)
        l0.addWidget(self.radiuses[0], 1, 2)
        l0.addWidget(QLabel("dr"), 0, 3)
        l0.addWidget(self.radiuses[1], 1, 3)
        l0.addWidget(QPushButton("Load from freeline", clicked=self._LoadFromFreeLine), 1, 4)
        lh = QVBoxLayout()
        lh.addLayout(self.axes[0])
        lh.addLayout(self.axes[1])
        lh.addLayout(l0)
        self.setLayout(lh)

    def getParameters(self):
        return {"center": [c.value() for c in self.center], "radiuses": [c.value() for c in self.radiuses], "axes": [c.getAxis() for c in self.axes]}

    def setParameters(self, center, radiuses, axes):
        for c, i in zip(self.center, center):
            c.setValue(i)
        for c, i in zip(self.radiuses, radiuses):
            c.setValue(i)
        for c, i in zip(self.axes, axes):
            c.setAxis(i)

    def _LoadFromFreeLine(self):
        c = Graph.active().canvas
        l = c.getAnnotations("line")[0]
        pos = np.array(c.getAnnotLinePosition(l)).T
        for c, i in zip(self.center, pos[0]):
            c.setValue(i)
        r = np.linalg.norm(pos[0] - pos[1])
        self.radiuses[0].setValue(r)
        self.radiuses[1].setValue(r / 100)


filterGroups['Sum, Mean, Median...'] = IntegrationSetting
