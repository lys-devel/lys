from ..filter.MatrixMath import *
from ..filtersGUI import *
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


class SelectIndexSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._index = IndexLayout(dimension)
        self.setLayout(self._index)

    def GetFilter(self):
        return SelectIndexFilter(*self._index.getAxisAndIndex())

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SelectIndexFilter):
            return True

    def parseFromFilter(self, f):
        obj = SelectIndexSetting(None, self.dim, self.loader)
        axis, index = f.getParams()
        obj._index.setAxis(axis)
        obj._index.setValue(index)
        return obj


class IndexMathSetting(FilterSettingBase):
    _types = ["+", "-", "*", "/"]

    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
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

    def GetFilter(self):
        return IndexMathFilter(self._axis.getAxis(), self._combo.currentText(), self._index1.value(), self._index2.value())

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, IndexMathFilter):
            return True

    def parseFromFilter(self, f):
        obj = IndexMathSetting(None, self.dim, self.loader)
        axis, type, i1, i2 = f.getParams()
        obj._axis.setAxis(axis)
        obj._combo.setCurrentIndex(self._types.index(type))
        obj._index1.setValue(i1)
        obj._index2.setValue(i2)
        return obj


class TransposeSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
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

    def GetFilter(self):
        st = self.val.text()
        vals = st.replace(" ", "").split(",")
        return TransposeFilter([int(v) for v in vals])

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, TransposeFilter):
            return True

    def parseFromFilter(self, f):
        obj = TransposeSetting(None, self.dim, self.loader)
        axes = f.getParams()
        st = ""
        for ax in axes:
            st += str(ax) + ", "
        st = st[:-2]
        obj.val.setText(st)
        return obj


class SliceSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
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

    def GetFilter(self):
        slices = [[self._start[d].value(), self._stop[d].value(), self._step[d].value()] for d in range(self.dim)]
        return SliceFilter(slices)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SliceFilter):
            return True

    def parseFromFilter(self, f):
        obj = SliceSetting(None, self.dim, self.loader)
        params = f.getParams()
        for d in range(self.dim):
            obj._start[d].setValue(params[d][0])
            obj._stop[d].setValue(params[d][1])
            obj._step[d].setValue(params[d][2])
        return obj


filterGroups['Wave Process'] = MatrixMathSetting
