from ..filter.Region import *
from ..filtersGUI import *
from .CommonWidgets import *


class RegionSelectWidget(QGridLayout):
    loadClicked = pyqtSignal(object)

    def __init__(self, parent, dim, loader=None):
        super().__init__()
        self.dim = dim
        self.loader = loader
        self.__initLayout(dim, loader)

    def __initLayout(self, dim, loader):
        self.__loadPrev = QPushButton('Load from Graph', clicked=self.__loadFromPrev)
        if loader is None:
            self.loadClicked.connect(self.__load)
        else:
            self.loadClicked.connect(loader)
        self.addWidget(self.__loadPrev, 0, 0)

        self.addWidget(QLabel("from"), 1, 0)
        self.addWidget(QLabel("to"), 2, 0)
        self.start = [QSpinBox() for d in range(dim)]
        self.end = [QSpinBox() for d in range(dim)]
        i = 1
        for s, e in zip(self.start, self.end):
            s.setRange(0, 10000)
            e.setRange(0, 10000)
            self.addWidget(QLabel("Axis" + str(i)), 0, i)
            self.addWidget(s, 1, i)
            self.addWidget(e, 2, i)
            i += 1

    def __loadFromPrev(self, arg):
        self.loadClicked.emit(self)

    def __load(self, obj):
        c = Graph.active().canvas
        if c is not None:
            r = c.SelectedRange()
            w = c.getWaveData()[0].wave
            p1 = w.posToPoint(r[0])
            p2 = w.posToPoint(r[1])
            self.setRegion(0, (p1[0], p2[0]))
            self.setRegion(1, (p1[1], p2[1]))

    def setRegion(self, axis, range):
        if axis < len(self.start):
            self.start[axis].setValue(min(range[0], range[1]))
            self.end[axis].setValue(max(range[0], range[1]))

    def getRegion(self):
        return [[s.value(), e.value()] for s, e in zip(self.start, self.end)]


class NormalizeSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self.__parent = parent
        self.range = RegionSelectWidget(self, dim, loader)
        self.combo = QComboBox()
        self.combo.addItem("Whole")
        for d in range(dim):
            self.combo.addItem("Axis" + str(d + 1))

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel("Axis"))
        vbox.addWidget(self.combo)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addLayout(self.range)
        self.setLayout(hbox)

    def GetFilter(self):
        return NormalizeFilter(self.range.getRegion(), self.combo.currentIndex() - 1)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, NormalizeFilter):
            return True

    def parseFromFilter(self, f):
        obj = NormalizeSetting(None, self.dim, self.loader)
        region, axis = f.getParams()
        obj.combo.setCurrentIndex(axis + 1)
        for i, r in enumerate(region):
            obj.range.setRegion(i, r)
        return obj


class SelectRegionSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self.__parent = parent
        self.range = RegionSelectWidget(self, dim, loader)
        self.setLayout(self.range)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SelectRegionFilter):
            return True

    def GetFilter(self):
        return SelectRegionFilter(self.range.getRegion())

    def parseFromFilter(self, f):
        obj = SelectRegionSetting(None, self.dim, self.loader)
        region = f.getRegion()
        for i, r in enumerate(region):
            obj.range.setRegion(i, r)
        return obj


filterGroups['Select region'] = SelectRegionSetting
filterGroups['Normalization'] = NormalizeSetting
