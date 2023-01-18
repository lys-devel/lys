import numpy as np

from lys import DaskWave
from lys.Qt import QtWidgets
from lys.filters import FilterInterface, FilterSettingBase, filterGUI, addFilter
from lys.widgets import AxisSelectionLayout


class SelectIndexFilter(FilterInterface):
    """
    Indexing of data.

    For example, when *axis* = 1 and index=4, data[:,4] is returned.

    For more complex indexing, use :class:`SliceFilter`.

    Args:
        index(int): index to be evaluated.
        axis(int): axis to be evaluated.
    """

    def __init__(self, index, axis=0):
        self._axis = axis
        self._index = index

    def _execute(self, wave, **kwargs):
        axes = list(wave.axes)
        axes.pop(self._axis)
        sl = [slice(None)] * wave.data.ndim
        sl[self._axis] = self._index
        data = wave.data[tuple(sl)]
        return DaskWave(data, *axes, **wave.note)

    def getParameters(self):
        return {"axis": self._axis, "index": self._index}

    def getRelativeDimension(self):
        return -1


class SliceFilter(FilterInterface):
    """
    Slicing waves.

    Args:
        slices(sequence of slice object): slices to be applied.

    Example::

        from lys import Wave, filters

        w = Wave([[1, 2, 3], [4, 5, 6]], [7, 8], [9, 10, 11], name="wave")
        f = filters.SliceFilter([slice(None), slice(1, 3)])

        result = f.execute(w)
        print(result.data, result.x, result.y) # [[2, 3], [5, 6]], [7, 8], [10, 11]

    """

    def __init__(self, slices):
        self._sl = []
        for s in slices:
            if s is None:
                self._sl.append(slice(None))
            elif isinstance(s, slice):
                self._sl.append(s)
            elif isinstance(s, int):
                self._sl.append(slice(s, s, 1))
            elif isinstance(s, list) or isinstance(s, tuple):
                self._sl.append(slice(*s))

    def _execute(self, wave, **kwargs):
        slices = self._sl
        axes = []
        for i, s in enumerate(slices):
            if not self._isChangeDim(s):
                if wave.axisIsValid(i):
                    axes.append(wave.axes[i][s])
                else:
                    axes.append(None)
        for i, s in enumerate(slices):
            if self._isChangeDim(s):
                slices[i] = s.start
        return DaskWave(wave.data[tuple(slices)], *axes, **wave.note)

    def _isChangeDim(self, slice):
        if slice.start is None:
            return False
        if slice.start == slice.stop:
            return True
        return False

    def getParameters(self):
        return {"slices": self._sl}

    def getRelativeDimension(self):
        return -np.sum([1 for s in self._sl if s.start == s.stop])


class IndexMathFilter(FilterInterface):
    """
    Calculate wave[*index1*] op wave[*index2*].

    Args:
        axis(int): axis to be calculated
        type('+' or '-' or '\*' or '/'): operator type
        index1(int): index1 along *axis*
        index2(int): index2 along *axis*

    """

    def __init__(self, axis, type, index1, index2):
        self._type = type
        self._axis = axis
        self._index1 = index1
        self._index2 = index2

    def _execute(self, wave, **kwargs):
        axes = list(wave.axes)
        axes.pop(self._axis)
        sl1 = [slice(None)] * wave.data.ndim
        sl1[self._axis] = self._index1
        sl2 = [slice(None)] * wave.data.ndim
        sl2[self._axis] = self._index2
        if self._type == "+":
            data = wave.data[tuple(sl1)] + wave.data[tuple(sl2)]
        if self._type == "-":
            data = wave.data[tuple(sl1)] - wave.data[tuple(sl2)]
        if self._type == "*":
            data = wave.data[tuple(sl1)] * wave.data[tuple(sl2)]
        if self._type == "/":
            data = wave.data[tuple(sl1)] / wave.data[tuple(sl2)]
        wave.axes = axes
        return DaskWave(data, *axes, **wave.note)

    def getParameters(self):
        return {"axis": self._axis, "type": self._type, "index1": self._index1, "index2": self._index2}

    def getRelativeDimension(self):
        return -1


class TransposeFilter(FilterInterface):
    """
    Tranpose data by np.transpose

    Args:
        axes(sequence of int): order of axes.

    Example::

        from lys import Wave, filters

        w = Wave([[1, 2, 3], [4, 5, 6]])
        f = filters.TransposeFilter(axes=[1, 0])

        result = f.execute(w)
        print(result.data)  # [[1, 4], [2, 5], [3, 6]]
    """

    def __init__(self, axes):
        self._axes = axes

    def _execute(self, wave, **kwargs):
        data = wave.data.transpose(self._axes)
        axes = [wave.axes[i] for i in self._axes]
        return DaskWave(data, *axes, **wave.note)

    def getParameters(self):
        return {"axes": self._axes}


class _IndexLayout(QtWidgets.QHBoxLayout):
    def __init__(self, dim):
        super().__init__()
        self._axis = AxisSelectionLayout("Axis", dim)
        self._index = QtWidgets.QSpinBox()
        self.addLayout(self._axis)
        self.addWidget(QtWidgets.QLabel("Index"))
        self.addWidget(self._index)

    def getAxisAndIndex(self):
        return self._axis.getAxis(), self._index.value()

    def setAxis(self, axis):
        self._axis.setAxis(axis)

    def setValue(self, value):
        self._index.setValue(value)


@filterGUI(SelectIndexFilter)
class _SelectIndexSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._index = _IndexLayout(dimension)
        self.setLayout(self._index)

    def getParameters(self):
        axis, index = self._index.getAxisAndIndex()
        return {"axis": axis, "index": index}

    def setParameters(self, axis, index):
        self._index.setAxis(axis)
        self._index.setValue(index)


@filterGUI(IndexMathFilter)
class _IndexMathSetting(FilterSettingBase):
    _types = ["+", "-", "*", "/"]

    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._combo = QtWidgets.QComboBox()
        self._combo.addItems(self._types)
        self._axis = AxisSelectionLayout("Axis", dimension)
        self._index1 = QtWidgets.QSpinBox()
        self._index2 = QtWidgets.QSpinBox()
        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(QtWidgets.QLabel("Indices"))
        h1.addWidget(self._index1)
        h1.addWidget(self._combo)
        h1.addWidget(self._index2)
        layout = QtWidgets.QVBoxLayout()
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


@filterGUI(TransposeFilter)
class _TransposeSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        lay = QtWidgets.QHBoxLayout()
        self.val = QtWidgets.QLineEdit()
        st = ""
        for d in range(dimension):
            st += str(d) + ", "
        self.val.setText(st[:-2])

        lay.addWidget(self.val)
        lay.addWidget(QtWidgets.QPushButton("Reverse", clicked=self._click))
        self.setLayout(lay)

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


@filterGUI(SliceFilter)
class _SliceSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        lay = QtWidgets.QGridLayout()
        lay.addWidget(QtWidgets.QLabel("Start"), 0, 1)
        lay.addWidget(QtWidgets.QLabel("Stop"), 0, 2)
        lay.addWidget(QtWidgets.QLabel("Step"), 0, 3)
        for d in range(dimension):
            lay.addWidget(QtWidgets.QLabel("Axis" + str(d)), 1 + d, 0)

        self._start = [QtWidgets.QSpinBox() for d in range(dimension)]
        self._stop = [QtWidgets.QSpinBox() for d in range(dimension)]
        self._step = [QtWidgets.QSpinBox() for d in range(dimension)]
        for d in range(dimension):
            self._start[d].setRange(-1000000, 1000000)
            self._stop[d].setRange(-1000000, 1000000)
            self._step[d].setRange(-1000000, 1000000)
            self._step[d].setValue(1)
            self._start[d].valueChanged.connect(self.dimensionChanged)
            self._stop[d].valueChanged.connect(self.dimensionChanged)
            self._step[d].valueChanged.connect(self.dimensionChanged)
            lay.addWidget(self._start[d], 1 + d, 1)
            lay.addWidget(self._stop[d], 1 + d, 2)
            lay.addWidget(self._step[d], 1 + d, 3)
        self.setLayout(lay)

    def getParameters(self):
        return {"slices": [[self._start[d].value(), self._stop[d].value(), self._step[d].value()] for d in range(self.dim)]}

    def setParameters(self, slices):
        for d in range(self.dim):
            self._start[d].setValue(slices[d].start)
            self._stop[d].setValue(slices[d].stop)
            self._step[d].setValue(slices[d].step)


addFilter(SelectIndexFilter, gui=_SelectIndexSetting, guiName="Select Index", guiGroup="Indices")
addFilter(IndexMathFilter, gui=_IndexMathSetting, guiName="Inter-index calc.", guiGroup="Indices")
addFilter(TransposeFilter, gui=_TransposeSetting, guiName="Transpose", guiGroup="Indices")
addFilter(SliceFilter, gui=_SliceSetting, guiName="Slicing", guiGroup="Resize and interpolation")
