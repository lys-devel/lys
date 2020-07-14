from ..filter.MatrixMath import *
from ..filtersGUI import *
from .CommonWidgets import *


class MatrixMathSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Select Index': SelectIndexSetting,
            'Index Math': IndexMathSetting,
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


filterGroups['Wave Process'] = MatrixMathSetting
