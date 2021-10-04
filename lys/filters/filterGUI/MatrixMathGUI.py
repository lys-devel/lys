from lys import filters
from ..filtersGUI import filterGroups, FilterGroupSetting, FilterSettingBase, filterGUI
from .CommonWidgets import *


class MatrixMathSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Select Index': SelectIndexSetting,
            'Index Math': IndexMathSetting,
            'Transpose': TransposeSetting,
            'Slice': SliceSetting,
        }
        return d


class IndexLayout(QHBoxLayout):
    def __init__(self, dim):
        super().__init__()
        self._axis = AxisSelectionLayout("Axis", dim)
        self._index = QSpinBox()
        self.addLayout(self._axis)
        self.addWidget(QLabel("Index"))
        self.addWidget(self._index)

    def getAxisAndIndex(self):
        return self._axis.getAxis(), self._index.value()

    def setAxis(self, axis):
        self._axis.setAxis(axis)

    def setValue(self, value):
        self._index.setValue(value)


@filterGUI(filters.SelectIndexFilter)
class SelectIndexSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._index = IndexLayout(dimension)
        self.setLayout(self._index)

    def getParameters(self):
        axis, index = self._index.getAxisAndIndex()
        return {"axis": axis, "index": index}

    def setParameters(self, axis, index):
        self._index.setAxis(axis)
        self._index.setValue(index)


@filterGUI(filters.IndexMathFilter)
class IndexMathSetting(FilterSettingBase):
    _types = ["+", "-", "*", "/"]

    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._combo = QComboBox()
        self._combo.addItems(self._types)
        self._axis = AxisSelectionLayout("Axis", dimension)
        self._index1 = QSpinBox()
        self._index2 = QSpinBox()
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Indices"))
        h1.addWidget(self._index1)
        h1.addWidget(self._combo)
        h1.addWidget(self._index2)
        layout = QVBoxLayout()
        layout.addLayout(self._axis)
        layout.addLayout(h1)
        self.setLayout(layout)

    def getParameters(self):
        return {"axis": self._axis.getAxis(), "type": self._combo.currentText(), "index1": self._index1.value(), "index2": self._index2.value()}

    def setParameters(self, axis, type, index1, index2):
        self._axis.setAxis(axis)
        self._combo.setCurrentIndex(self._types.index(type))
        self._index1.setValue(index1)
        self._index2.setValue(index2)


@filterGUI(filters.TransposeFilter)
class TransposeSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        l = QHBoxLayout()
        self.val = QLineEdit()
        st = ""
        for d in range(dimension):
            st += str(d) + ", "
        self.val.setText(st[:-2])

        l.addWidget(self.val)
        l.addWidget(QPushButton("Reverse", clicked=self._click))
        self.setLayout(l)

    def _click(self):
        vals = [int(v) for v in self.val.text().replace(" ", "").split(",")]
        st = ""
        for v in reversed(vals):
            st += str(v) + ", "
        self.val.setText(st[:-2])

    def getParameters(self):
        return {"axes": eval(self.val.text())}

    def setParameters(self, axes):
        st = ""
        for ax in axes:
            st += str(ax) + ", "
        st = st[:-2]
        self.val.setText(st)


@filterGUI(filters.SliceFilter)
class SliceSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        l = QGridLayout()
        l.addWidget(QLabel("Start"), 0, 1)
        l.addWidget(QLabel("Stop"), 0, 2)
        l.addWidget(QLabel("Step"), 0, 3)
        for d in range(dimension):
            l.addWidget(QLabel("Axis" + str(d)), 1 + d, 0)

        self._start = [QSpinBox() for d in range(dimension)]
        self._stop = [QSpinBox() for d in range(dimension)]
        self._step = [QSpinBox() for d in range(dimension)]
        for d in range(dimension):
            self._start[d].setRange(-1000000, 1000000)
            self._stop[d].setRange(-1000000, 1000000)
            self._step[d].setRange(-1000000, 1000000)
            self._step[d].setValue(1)
            l.addWidget(self._start[d], 1 + d, 1)
            l.addWidget(self._stop[d], 1 + d, 2)
            l.addWidget(self._step[d], 1 + d, 3)
        self.setLayout(l)

    def getParameters(self):
        return {"slices": [[self._start[d].value(), self._stop[d].value(), self._step[d].value()] for d in range(self.dim)]}

    def setParameters(self, slices):
        for d in range(self.dim):
            self._start[d].setValue(slices[d].start)
            self._stop[d].setValue(slices[d].stop)
            self._step[d].setValue(slices[d].step)


filterGroups['Wave Process'] = MatrixMathSetting
