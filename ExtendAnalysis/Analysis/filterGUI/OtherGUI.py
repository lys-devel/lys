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


class FreeLineSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self.__initlayout()

    def __initlayout(self):
        h3 = QHBoxLayout()
        self.width = QSpinBox()
        self.width.setValue(3)
        self.load = QPushButton("Load from Graph", clicked=self.__load)
        h3.addWidget(QLabel("Width"))
        h3.addWidget(self.width)
        h3.addWidget(self.load)
        self.axis1 = AxisSelectionLayout("Axis 1", self.dim, 0)
        self.from1 = ScientificSpinBox()
        self.to1 = ScientificSpinBox()
        h1 = QHBoxLayout()
        h1.addLayout(self.axis1)
        h1.addWidget(self.from1)
        h1.addWidget(self.to1)
        self.axis2 = AxisSelectionLayout("Axis 2", self.dim, 1)
        self.from2 = ScientificSpinBox()
        self.to2 = ScientificSpinBox()
        h2 = QHBoxLayout()
        h2.addLayout(self.axis2)
        h2.addWidget(self.from2)
        h2.addWidget(self.to2)
        self._layout = QVBoxLayout()
        self._layout.addLayout(h3)
        self._layout.addLayout(h1)
        self._layout.addLayout(h2)
        self.setLayout(self._layout)

    def __load(self):
        g = Graph.active()
        if g is None:
            return
        c = g.canvas
        lines = c.getAnnotations("line")
        if len(lines) == 0:
            return
        if self.dim != 2:
            d = AxesSelectionDialog(self.dim)
            value = d.exec_()
            if value:
                ax = d.getAxes()
                self.axis1.setAxis(ax[0])
                self.axis2.setAxis(ax[1])
            else:
                return
        l = lines[0]
        p = c.getAnnotLinePosition(l)
        self.from1.setValue(p[0][0])
        self.to1.setValue(p[0][1])
        self.from2.setValue(p[1][0])
        self.to2.setValue(p[1][1])

    def GetFilter(self):
        axes = [self.axis1.getAxis(), self.axis2.getAxis()]
        range = [[self.from1.value(), self.to1.value()], [self.from2.value(), self.to2.value()]]
        width = self.width.value()
        return FreeLineFilter(axes, range, width)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, FreeLineFilter):
            return True

    def parseFromFilter(self, f):
        obj = FreeLineSetting(None, self.dim, self.loader)
        axes, range, width = f.getParams()
        obj.axis1.setAxis(axes[0])
        obj.axis2.setAxis(axes[1])
        obj.from1.setValue(range[0][0])
        obj.to1.setValue(range[0][1])
        obj.from2.setValue(range[1][0])
        obj.to2.setValue(range[1][1])
        obj.width.setValue(width)
        return obj


class PeakSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._combo = QComboBox()
        self._combo.addItem("ArgRelMax")
        self._combo.addItem("ArgRelMin")
        self._order = QSpinBox()
        self._axis = AxisSelectionLayout("Axis", dimension)
        h1 = QHBoxLayout()
        h1.addWidget(self._combo)
        h1.addWidget(QLabel("order"))
        h1.addWidget(self._order)
        layout = QVBoxLayout()
        layout.addLayout(self._axis)
        layout.addLayout(h1)
        self.setLayout(layout)

    def GetFilter(self):
        return PeakFilter(self._axis.getAxis(), self._order.value(), self._combo.currentText())

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, PeakFilter):
            return True

    def parseFromFilter(self, f):
        obj = PeakSetting(None, self.dim, self.loader)
        params = f.getParams()
        obj._axis.setAxis(params[0])
        obj._order.setValue(params[1])
        if params[2] == "ArgRelMax":
            obj._combo.setCurrentIndex(0)
        else:
            obj._combo.setCurrentIndex(1)
        return obj


filterGroups['*Interpolation'] = InterpSetting
filterGroups['Reduce size'] = ReduceSizeSetting
filterGroups['Cut along line'] = FreeLineSetting
filterGroups['Find Peak'] = PeakSetting
