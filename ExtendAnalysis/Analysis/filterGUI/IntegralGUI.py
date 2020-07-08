from ..filter.Region import *
from ..filtersGUI import *
from .CommonWidgets import *
from ExtendAnalysis import ScientificSpinBox


class IntegrationSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Axis': IntegralSetting,
            'Circle': CircleSetting,
        }
        return d


class IntegralSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self.__parent = parent
        self.range = RegionSelectWidget(self, dim, loader)
        self.setLayout(self.range)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, IntegralFilter):
            return True

    def GetFilter(self):
        return IntegralFilter(self.range.getRegion())

    def parseFromFilter(self, f):
        obj = IntegralSetting(None, self.dim, self.loader)
        region = f.getRegion()
        for i, r in enumerate(region):
            obj.range.setRegion(i, r)
        return obj


class CircleSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self.__parent = parent
        self.axes = [AxisSelectionLayout(
            "Axis1"), AxisSelectionLayout("Axis2")]
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
        l0.addWidget(QPushButton("Load from freeline",
                                 clicked=self._LoadFromFreeLine), 1, 4)
        lh = QVBoxLayout()
        lh.addLayout(self.axes[0])
        lh.addLayout(self.axes[1])
        lh.addLayout(l0)
        self.setLayout(lh)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, IntegralCircleFilter):
            return True

    def GetFilter(self):
        center = [c.value() for c in self.center]
        radiuses = [c.value() for c in self.radiuses]
        axes = [c.getAxis() for c in self.axes]
        return IntegralCircleFilter(center, radiuses, axes)

    def parseFromFilter(self, f):
        obj = CircleSetting(None, self.dim, self.loader)
        center, radius, axes = f.getParams()
        for c, i in zip(obj.center, center):
            c.setValue(i)
        for c, i in zip(obj.radiuses, radius):
            c.setValue(i)
        for c, i in zip(obj.axes, axes):
            c.setAxis(i)
        return obj

    def _LoadFromFreeLine(self):
        c = Graph.active().canvas
        l = c.getAnnotations("line")[0]
        pos = np.array(c.getAnnotLinePosition(l)).T
        for c, i in zip(self.center, pos[0]):
            c.setValue(i)
        r = np.linalg.norm(pos[0]-pos[1])
        self.radiuses[0].setValue(r)
        self.radiuses[1].setValue(r/100)


filterGroups['Integral'] = IntegrationSetting
