import numpy as np
from scipy.signal import argrelextrema
from scipy.ndimage import median_filter

from lys import DaskWave
from lys.Qt import QtWidgets
from lys.filters import FilterInterface, FilterSettingBase, filterGUI, addFilter
from lys.widgets import AxisSelectionLayout


class PeakFilter(FilterInterface):
    def __init__(self, axis, order, type="ArgRelMax", size=1):
        self._order = order
        self._type = type
        self._axis = axis
        self._size = size

    def _execute(self, wave, *args, **kwargs):
        if self._type == "ArgRelMax":
            def f(x): return _relmax(x, self._order, self._size)
        else:
            def f(x): return _relmin(x, self._order, self._size)
        axes = [ax for ax in wave.axes]
        axes[self._axis] = None
        uf = self._generalizedFunction(wave, f, signature="(i)->(j)", axes=[(self._axis,), (self._axis)], output_dtypes=float, output_sizes={"j": self._size})
        return DaskWave(uf(wave.data), *axes, **wave.note)

    def getParameters(self):
        return {"axis": self._axis, "order": self._order, "type": self._type, "size": self._size}


def _relmax(x, order, size):
    data = argrelextrema(x, np.greater_equal, order=order)[0]
    res = [d for d in data if d != 0 and d != len(x) - 1]
    while len(res) < size:
        res.append(0)
    return np.array(res[:size])


def _relmin(x, order, size):
    data = argrelextrema(x, np.less_equal, order=order)[0]
    res = [d for d in data if d != 0 and d != len(x) - 1]
    res = list(data)
    while len(res) < size:
        res.append(0)
    return np.array(res[:size])


class PeakPostFilter(FilterInterface):
    def __init__(self, axis, medSize):
        self._axis = axis
        self._size = medSize

    def _execute(self, wave, *args, **kwargs):
        uf = self._generalizedFunction(wave, _find4D, signature="(i,j,k,l),(m)->(i,j,k,l)", axes=[(0, 1, 2, 3), (0), (0, 1, 2, 3)])
        return DaskWave(uf(wave.data, np.array(self._size)), *wave.axes, **wave.note)

    def getParameters(self):
        return {"axis": self._axis, "medSize": self._size}


def _find4D(data, medSize):
    edge = [_findNearest(data[0, :, :, 0], np.median(data[0, :, n, 0])) for n in range(data.shape[2])]
    plane = [_findNearest(data.transpose(1, 0, 2, 3)[:, :, :, 0], e, medSize[0]).transpose(1, 0) for e in edge]
    volume = [_findNearest(data.transpose(0, 1, 3, 2), p, medSize[1]) for p in plane]
    return np.array(volume).transpose(1, 2, 0, 3)


def _findNearest(data, reference, medSize=1):  # reference: n-dim array, data: (n+2)-dim array, return (n+1)-dim array
    ref = median_filter(np.array(reference), medSize)
    mesh = np.meshgrid(*[range(x) for x in ref.shape], indexing="ij")
    res = []
    for i in range(data.shape[-2]):
        sl = [slice(None)] * (data.ndim)
        sl[-2] = i
        tile = tuple([data.shape[-1]] + [1] * (data.ndim - 2))
        order = list(range(1, ref.ndim + 1)) + [0]
        diff = np.abs(data[tuple(sl)] - np.tile(ref, tile).transpose(*order))
        index = np.argmin(diff, axis=-1)
        sl2 = mesh + [i] + [index]
        ref = data[tuple(sl2)]
        res.append(ref)
        ref = median_filter(ref, medSize)
    return np.array(res).transpose(order)


class PeakReorderFilter(FilterInterface):
    def __init__(self, peakAxis, scanAxis, medSize):
        self._peak = peakAxis
        self._scan = scanAxis
        self._size = medSize

    def _execute(self, wave, *args, **kwargs):
        axes = list(range(len(wave.data.shape)))
        axes.remove(self._peak)
        axes.remove(self._scan)
        axes = [self._peak, self._scan] + axes

        def f(x):
            return _reorder(x, self._size)
        uf = self._generalizedFunction(wave, f, signature="(i,j,k,l)->(i,j,k,l)", axes=[axes, axes])
        return DaskWave(uf(wave.data), *wave.axes, **wave.note)

    def getParameters(self):
        return {"peakAxis": self._peak, "scanAxis": self._scan, "medSize": self._size}


def _reorder(data, size):
    res = []
    for n in range(data.shape[0]):
        ref = data[n][0]
        mesh = np.meshgrid(*[range(x) for x in ref.shape], indexing="ij")
        tmp = [ref]
        for m in range(1, data.shape[1]):
            diff = np.abs(data[:, m] - median_filter(ref, size))
            index = np.argmin(diff, axis=0)
            ref = data[tuple([index, m, *mesh])]
            tmp.append(ref)
        res.append(np.array(tmp))
    return np.array(res)


@filterGUI(PeakFilter)
class _PeakSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._combo = QtWidgets.QComboBox()
        self._combo.addItems(["ArgRelMax", "ArgRelMin"])
        self._order = QtWidgets.QSpinBox()
        self._order.setValue(1)
        self._value = QtWidgets.QSpinBox()
        self._value.setValue(3)
        self._axis = AxisSelectionLayout("Axis", dimension)
        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(self._combo)
        h1.addWidget(QtWidgets.QLabel("order"))
        h1.addWidget(self._order)
        h1.addWidget(QtWidgets.QLabel("size"))
        h1.addWidget(self._value)
        layout = QtWidgets.QVBoxLayout()
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


@filterGUI(PeakPostFilter)
class _PeakPostSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._axis = AxisSelectionLayout("Find peak along axis (should be 2)", dimension)
        self._size1 = QtWidgets.QSpinBox()
        self._size1.setValue(15)
        self._size2 = QtWidgets.QSpinBox()
        self._size2.setValue(5)
        g = QtWidgets.QGridLayout()
        g.addWidget(QtWidgets.QLabel("Median along axis 0"), 0, 0)
        g.addWidget(self._size1, 0, 1)
        g.addWidget(QtWidgets.QLabel("Median along axis 3"), 1, 0)
        g.addWidget(self._size2, 1, 1)
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self._axis)
        layout.addLayout(g)
        self.setLayout(layout)

    def getParameters(self):
        return {"axis": self._axis.getAxis(), "medSize": (self._size1.value(), self._size2.value())}

    def setParameters(self, axis, medSize):
        self._axis.setAxis(axis)
        self._size1.setValue(medSize[0])
        self._size2.setValue(medSize[1])


@filterGUI(PeakReorderFilter)
class _PeakReorderSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._peak = AxisSelectionLayout("Peak index axis", dimension)
        self._scan = AxisSelectionLayout("Scan axis", dimension)

        self._size = QtWidgets.QSpinBox()
        self._size.setValue(9)
        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(QtWidgets.QLabel("Median size"))
        h1.addWidget(self._size)

        layout = QtWidgets.QVBoxLayout()
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


addFilter(PeakFilter, gui=_PeakSetting, guiName="Find Peak", guiGroup="Peak")
addFilter(PeakPostFilter, gui=_PeakPostSetting, guiName="Peak Postprocess", guiGroup="Peak")
addFilter(PeakReorderFilter, gui=_PeakReorderSetting, guiName="Peak Reorder", guiGroup="Peak")
