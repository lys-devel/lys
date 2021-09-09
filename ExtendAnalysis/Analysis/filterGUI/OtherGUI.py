
from ..filtersGUI import *
from .CommonWidgets import *


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
        self._value = QSpinBox()
        self._value.setValue(3)
        self._axis = AxisSelectionLayout("Axis", dimension)
        h1 = QHBoxLayout()
        h1.addWidget(self._combo)
        h1.addWidget(QLabel("order"))
        h1.addWidget(self._order)
        h1.addWidget(QLabel("size"))
        h1.addWidget(self._value)
        layout = QVBoxLayout()
        layout.addLayout(self._axis)
        layout.addLayout(h1)
        self.setLayout(layout)

    def GetFilter(self):
        return PeakFilter(self._axis.getAxis(), self._order.value(), self._combo.currentText(), self._value.value())

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, PeakFilter):
            return True

    def parseFromFilter(self, f):
        obj = PeakSetting(None, self.dim, self.loader)
        params = f.getParams()
        obj._axis.setAxis(params[0])
        obj._order.setValue(params[1])
        obj._value.setValue(params[3])
        if params[2] == "ArgRelMax":
            obj._combo.setCurrentIndex(0)
        else:
            obj._combo.setCurrentIndex(1)
        return obj


class PeakPostSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._axis = AxisSelectionLayout("Find peak along axis (should be 2)", dimension)
        self._size1 = QSpinBox()
        self._size1.setValue(15)
        self._size2 = QSpinBox()
        self._size2.setValue(5)
        g = QGridLayout()
        g.addWidget(QLabel("Median along axis 0"), 0, 0)
        g.addWidget(self._size1, 0, 1)
        g.addWidget(QLabel("Median along axis 3"), 1, 0)
        g.addWidget(self._size2, 1, 1)
        layout = QVBoxLayout()
        layout.addLayout(self._axis)
        layout.addLayout(g)
        self.setLayout(layout)

    def GetFilter(self):
        return PeakPostFilter(self._axis.getAxis(), (self._size1.value(), self._size2.value()))

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, PeakPostFilter):
            return True

    def parseFromFilter(self, f):
        obj = PeakPostSetting(None, self.dim, self.loader)
        axis, size = f.getParams()
        obj._axis.setAxis(axis)
        obj._size1.setValue(size[0])
        obj._size2.setValue(size[1])
        return obj


class PeakReorderSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._peak = AxisSelectionLayout("Peak index axis", dimension)
        self._scan = AxisSelectionLayout("Scan axis", dimension)

        self._size = QSpinBox()
        self._size.setValue(9)
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Median size"))
        h1.addWidget(self._size)

        layout = QVBoxLayout()
        layout.addLayout(self._peak)
        layout.addLayout(self._scan)
        layout.addLayout(h1)
        self.setLayout(layout)

    def GetFilter(self):
        return PeakReorderFilter(self._peak.getAxis(), self._scan.getAxis(), self._size.value())

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, PeakReorderFilter):
            return True

    def parseFromFilter(self, f):
        obj = PeakReorderSetting(None, self.dim, self.loader)
        peak, scan, size = f.getParams()
        obj._peak.setAxis(peak)
        obj._scan.setAxis(scan)
        obj._size.setValue(size)
        return obj


class FindPeakSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Find Peaks': PeakSetting,
            'Postprocess (3+1D)': PeakPostSetting,
            'Reorder': PeakReorderSetting,
        }
        return d


filterGroups['Cut along line'] = FreeLineSetting
filterGroups['Peak'] = FindPeakSetting
