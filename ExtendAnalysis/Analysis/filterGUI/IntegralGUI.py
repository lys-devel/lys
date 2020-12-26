from ..filter.Region import *
from ..filtersGUI import *
from .CommonWidgets import *
from ExtendAnalysis import ScientificSpinBox


class IntegrationSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Axis': IntegralAllSetting,
            'Range': IntegralSetting,
            'Circle': CircleSetting,
        }
        return d


class IntegralAllSetting(FilterSettingBase):
    _sumtypes = ["Sum", "Mean", "Median", "Max", "Min"]

    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self.__parent = parent
        self.type = QComboBox()
        self.type.addItems(self._sumtypes)
        self.axes = AxisCheckLayout(dim)
        lv = QVBoxLayout()
        lv.addWidget(self.type)
        lv.addLayout(self.axes)
        self.setLayout(lv)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, IntegralAllFilter):
            return True

    def GetFilter(self):
        return IntegralAllFilter(self.axes.GetChecked(), self.type.currentText())

    def parseFromFilter(self, f):
        obj = IntegralAllSetting(None, self.dim, self.loader)
        obj.axes.SetChecked(f.getAxes())
        obj.type.setCurrentIndex(self._sumtypes.index(f.getType()))
        return obj


class IntegralSetting(FilterSettingBase):
    _sumtypes = ["Sum", "Mean", "Median", "Max", "Min"]

    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self.__parent = parent
        self.type = QComboBox()
        self.type.addItems(self._sumtypes)
        self.range = RegionSelectWidget(self, dim, loader)
        lv = QVBoxLayout()
        lv.addWidget(self.type)
        lv.addLayout(self.range)
        self.setLayout(lv)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, IntegralFilter):
            return True

    def GetFilter(self):
        return IntegralFilter(self.range.getRegion(), self.type.currentText())

    def parseFromFilter(self, f):
        obj = IntegralSetting(None, self.dim, self.loader)
        region = f.getRegion()
        obj.type.setCurrentIndex(self._sumtypes.index(f.getType()))
        for i, r in enumerate(region):
            obj.range.setRegion(i, r)
        return obj


class CircleSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self.__parent = parent
        self.axes = [AxisSelectionLayout(
            "Axis1", dim=dim, init=0), AxisSelectionLayout("Axis2", dim=dim, init=1)]
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
        r = np.linalg.norm(pos[0] - pos[1])
        self.radiuses[0].setValue(r)
        self.radiuses[1].setValue(r / 100)


filterGroups['Sum, Mean, Median...'] = IntegrationSetting
