from lys import filters
from ..filtersGUI import filterGroups, FilterGroupSetting, FilterSettingBase, filterGUI
from .CommonWidgets import *


@filterGUI(filters.FreeLineFilter)
class FreeLineSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
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

    def getParameters(self):
        axes = [self.axis1.getAxis(), self.axis2.getAxis()]
        range = [[self.from1.value(), self.to1.value()], [self.from2.value(), self.to2.value()]]
        width = self.width.value()
        return {"axes": axes, "range": range, "width": width}

    def setParameters(self, axes, range, width):
        self.axis1.setAxis(axes[0])
        self.axis2.setAxis(axes[1])
        self.from1.setValue(range[0][0])
        self.to1.setValue(range[0][1])
        self.from2.setValue(range[1][0])
        self.to2.setValue(range[1][1])
        self.width.setValue(width)


@filterGUI(filters.PeakFilter)
class PeakSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._combo = QComboBox()
        self._combo.addItems(["ArgRelMax", "ArgRelMin"])
        self._order = QSpinBox()
        self._order.setValue(1)
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

    def getParameters(self):
        return {"axis": self._axis.getAxis(), "order": self._order.value(), "type": self._combo.currentText(), "size": self._value.value()}

    def setParameters(self, axis, order, type, size):
        self._axis.setAxis(axis)
        self._order.setValue(order)
        self._value.setValue(size)
        if type == "ArgRelMax":
            self._combo.setCurrentIndex(0)
        else:
            self._combo.setCurrentIndex(1)


@filterGUI(filters.PeakPostFilter)
class PeakPostSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
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

    def getParameters(self):
        return {"axis": self._axis.getAxis(), "medSize": (self._size1.value(), self._size2.value())}

    def setParameters(self, axis, medSize):
        self._axis.setAxis(axis)
        self._size1.setValue(medSize[0])
        self._size2.setValue(medSize[1])


@filterGUI(filters.PeakReorderFilter)
class PeakReorderSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
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

    def getParameters(self):
        return {"peakAxis": self._peak.getAxis(), "scanAxis": self._scan.getAxis(), "medSize": self._size.value()}

    def setParameters(self, peakAxis, scanAxis, medSize):
        self._peak.setAxis(peakAxis)
        self._scan.setAxis(scanAxis)
        self._size.setValue(medSize)


@filterGUI(filters.RechunkFilter)
class RechunkSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._chunk = [QSpinBox() for _ in range(dimension)]
        grid = QGridLayout()
        for i in range(dimension):
            grid.addWidget(QLabel("Dim " + str(i + 1)), 0, i)
            grid.addWidget(self._chunk[i], 1, i)
        self.setLayout(grid)

    def getParameters(self):
        return {"chunks": [s.value() for s in self._chunk]}

    def setParameters(self, chunks):
        for c, s in zip(chunks, self._chunk):
            s.setValue(c)


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
filterGroups['Rechunk'] = RechunkSetting
filterGroups['Peak'] = FindPeakSetting
