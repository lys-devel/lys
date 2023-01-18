import numpy as np
import dask.array as da

from lys import DaskWave, frontCanvas
from lys.filters import FilterInterface, FilterSettingBase, filterGUI, addFilter
from lys.Qt import QtWidgets
from lys.widgets import AxisCheckLayout, ScientificSpinBox, RegionSelectWidget, AxisSelectionLayout


def _getSumFunction(sumtype):
    if sumtype == "Sum":
        return da.sum
    elif sumtype == "Mean":
        return da.mean
    elif sumtype == "Max":
        return da.max
    elif sumtype == "Min":
        return da.min
    elif sumtype == "Median":
        return da.median


class IntegralAllFilter(FilterInterface):
    """
    Integrate wave along *axes* (implementation of np.sum, mean, max, min, and median in lys)

    See :class:`.FilterInterface.FilterInterface` for general description of Filters.

    Args:
        axes(list of int): axes to be integrated
        sumtype('Sum', 'Mean', 'Max', 'Min', or 'Median')

    Example::

        from lys import Wave, filters
        import numpy as np

        w = Wave(np.ones(3,4), [2,3,4], [5,6,7,8])
        f = filters.IntegralAllFilter(axes=[0], sumtype="Sum")
        result = f.execute(w)

        print(result.data) # [3,3,3,3]
        print(result.x)    # [5,6,7,8]

    See also:
        :class:`IntegralFilter`

    """

    def __init__(self, axes, sumtype):
        self._axes = axes
        self._sumtype = sumtype

    def _execute(self, wave, *args, **kwargs):
        func = _getSumFunction(self._sumtype)
        data = func(wave.data, axis=tuple(self._axes))
        ax = [wave.axes[i] for i in range(len(wave.axes)) if i not in self._axes]
        return DaskWave(data, *ax, **wave.note)

    def getParameters(self):
        return {"axes": self._axes, "sumtype": self._sumtype}

    def getRelativeDimension(self):
        return -len(self._axes)


class IntegralFilter(FilterInterface):
    """
    Integrate wave.

    Range of integration is specified by *range*.

    Note that the *range* is specified in the units of *axes* of (Dask)Wave.
    If axes is not specified, *range* should be specified by indice.

    See :class:`.FilterInterface.FilterInterface` for general description of Filters.

    Args:
        range(list of tuple of size 2): region to be integrated
        sumtype('Sum', 'Mean', 'Max', 'Min', or 'Median')

    Example::

        from lys import Wave, filters
        import numpy as np

        w = Wave(np.ones([5, 5, 5]), [1, 2, 3, 4, 5], [1, 2, 3, 4, 5], [2, 3, 4, 5, 6])
        f = filters.IntegralFilter([(1, 4), (2, 4), (0, 0)], sumtype="Sum")
        result = f.execute(w)

        print(result.data)  # [6, 6, 6, 6, 6]
        print(result.x)     # [2, 3, 4, 5, 6]


    See also:
        :class:`IntegralAllFilter`

    """

    def __init__(self, range, sumtype):
        self._range = range
        self._sumtype = sumtype

    def _execute(self, wave, *args, **kwargs):
        key, sumaxes = self._getIndexAnsSumAxes(wave, self._range)
        axes = []
        for i in range(wave.ndim):
            if i not in sumaxes:
                if wave.axisIsValid(i):
                    axes.append(wave.axes[i])
                else:
                    axes.append(None)
        func = _getSumFunction(self._sumtype)
        return DaskWave(func(wave.data[key], axis=tuple(sumaxes)), *axes, **wave.note)

    def _getIndexAnsSumAxes(self, wave, rang):
        sl = []
        sumaxes = []
        for i, r in enumerate(rang):
            if r is None:
                sl.append(slice(None))
            elif r[0] == 0 and r[1] == 0:
                sl.append(slice(None))
            else:
                ind = wave.posToPoint(r, axis=i)
                sl.append(slice(*ind))
                sumaxes.append(i)
        key = tuple(sl)
        return key, tuple(sumaxes)

    def getParameters(self):
        return {"range": self._range, "sumtype": self._sumtype}

    def getRelativeDimension(self):
        return -len([r for r in self._range if r[0] != 0 or r[1] != 0])


class IntegralCircleFilter(FilterInterface):
    """
    Circular integration of wave.

    Circularly integrate *f*(*x*,*y*) and returns *f*(*r*).

    This filter is under development.

    See :class:`.FilterInterface.FilterInterface` for general description of Filters.

    Args:
        center(tuple of size 2): position where *r* = 0
        radiuses(tuple of size 2):
        axes(tuple of size 2): axes to be integrated, i.e. (x,y)

    """

    def __init__(self, center, radiuses, axes=(0, 1)):
        self._center = center
        self._radiuses = radiuses
        self._axes = axes

    def _execute(self, wave, *args, **kwargs):
        region, rad = _translate_unit(wave, self._center, self._radiuses, self._axes)
        gumap = da.gufunc(_integrate_tangent, signature="(i,j),(p)->(m)",
                          output_dtypes=wave.data.dtype, vectorize=True, axes=[tuple(self._axes), (0,), (min(self._axes),)], allow_rechunk=True, output_sizes={"m": int(region[3] / region[4])})
        res = gumap(wave.data, da.from_array(region))
        axes = self.__makeAxes(wave, *rad, self._axes)
        return DaskWave(res, *axes, **wave.note)

    def __makeAxes(self, wave, r, dr, axes):
        result = list(np.array(wave.axes))
        result.pop(max(*axes))
        result.pop(min(*axes))
        result.insert(min(*axes), np.linspace(0, r, int(r / dr)))
        return result

    def getParameters(self):
        return {"center": self._center, "radiuses": self._radiuses, "axes": self._axes}

    def getRelativeDimension(self):
        return -1


def _translate_unit(wave, center, radiuses, axes):
    cx = wave.posToPoint(center[0], axis=axes[0])
    cy = wave.posToPoint(center[1], axis=axes[1])
    r = np.abs(wave.posToPoint(center[0] + radiuses[0], axis=axes[0]) - cx)
    dr = max(np.abs(wave.posToPoint(center[0] + radiuses[1], axis=axes[0]) - cx), 1)
    dr = int(dr)
    r = np.floor(r / dr) * dr
    pdr = np.abs(wave.pointToPos(dr, axis=axes[0]) - wave.pointToPos(0, axis=axes[0]))
    pr = np.abs(wave.pointToPos(r, axis=axes[0]) - wave.pointToPos(0, axis=axes[0]))
    return (cx, cy, 0, r, dr), (pr, pdr)


def _integrate_tangent(data, region):
    if len(data) <= 2:
        return np.empty((1,))
    dr = region[4]
    data = [_integrate_circle(data, (int(region[0]), int(region[1]), int(r), int(r + dr)))
            for r in range(int(region[2]), int(region[3]), int(dr))]
    return np.array(data)


def _integrate_circle(data, region):
    cx = region[0]
    cy = region[1]
    R1 = region[2]
    R2 = region[3]
    res = 0
    n = 0
    for px in _calcDonutPixels(R1, R2):
        a = abs(px[0]) - 0.5
        b = abs(px[1]) - 0.5
        if a < b:
            a, b = b, a
        y, x = cx + px[0], cy + px[1]
        if x > 0 and y > 0 and x < data.shape[1] and y < data.shape[0]:
            if not np.isnan(data[y, x]):
                rat = _calcArea(a, b, R2) - _calcArea(a, b, R1)
                res += data[y, x] * rat
                n += rat
    if n == 0:
        n = 1

    return res / n


def _calcArea(a, b, r):
    if r == 0:
        return 0
    if np.sqrt((a + 1) * (a + 1) + (b + 1) * (b + 1)) <= r:
        return 1
    elif np.sqrt(a * a + b * b) <= r and np.sqrt(a * a + (b + 1) * (b + 1)) >= r:
        b1 = np.sqrt(r * r - a * a)
        return _int(r, b, b1) - a * (b1 - b)
    elif np.sqrt(a * a + (b + 1) * (b + 1)) <= r and np.sqrt((a + 1) * (a + 1) + b * b) >= r:
        return _int(r, b, b + 1) - a
    elif np.sqrt((a + 1) * (a + 1) + b * b) <= r and np.sqrt((a + 1) * (a + 1) + (b + 1) * (b + 1)) > r:
        b1 = np.sqrt(r * r - (a + 1) * (a + 1))
        return (b1 - b) + _int(r, b1, b + 1) - a * (b + 1 - b1)
    elif np.sqrt(a * a + b * b) > r:
        return 0
# calc int_a^b sqrt(r^2-x^2) dx


def _int(r, a, b):
    return 0.5 * (b * np.sqrt(r * r - b * b) + r * r * np.arcsin(b / r) - a * np.sqrt(r * r - a * a) - r * r * np.arcsin(a / r))


def _calcDonutPixels(R1, R2):
    res = []
    for y1 in range(-int(np.floor(R2 + 0.5)), int(np.floor(R2 + 0.5) + 1)):
        y1_R1 = _calcCross(y1, R1)
        y1_R2 = _calcCross(y1, R2)
        y1p_R1 = _calcCross(y1 + 0.5, R1)
        y1p_R2 = _calcCross(y1 + 0.5, R2)
        y1m_R1 = _calcCross(y1 - 0.5, R1)
        y1m_R2 = _calcCross(y1 - 0.5, R2)
        if y1m_R1 * y1p_R1 == 0:
            xmin = 0
        else:
            xmin = int(np.round(np.amin([y1_R1, y1p_R1, y1m_R1])))
        xmax = int(np.round(np.amax([y1_R2, y1p_R2, y1m_R2])))
        for x1 in range(xmin, xmax + 1):
            res.append((x1, y1))
        for x1 in range(-xmax, -xmin + 1):
            if x1 != 0:
                res.append((x1, y1))
    return res


def _calcCross(y, R):
    if abs(y) > R:
        return 0
    else:
        return np.sqrt(R * R - y * y)


@filterGUI(IntegralAllFilter)
class _IntegralAllSetting(FilterSettingBase):
    _sumtypes = ["Sum", "Mean", "Median", "Max", "Min"]

    def __init__(self, dim):
        super().__init__(dim)
        self.type = QtWidgets.QComboBox()
        self.type.addItems(self._sumtypes)
        self.axes = AxisCheckLayout(dim)
        self.axes.stateChanged.connect(self.dimensionChanged)
        lv = QtWidgets.QVBoxLayout()
        lv.addWidget(self.type)
        lv.addLayout(self.axes)
        self.setLayout(lv)

    def getParameters(self):
        return {"axes": self.axes.GetChecked(), "sumtype": self.type.currentText()}

    def setParameters(self, axes, sumtype):
        self.axes.SetChecked(axes)
        self.type.setCurrentIndex(self._sumtypes.index(sumtype))


@filterGUI(IntegralFilter)
class _IntegralSetting(FilterSettingBase):
    _sumtypes = ["Sum", "Mean", "Median", "Max", "Min"]

    def __init__(self, dim):
        super().__init__(dim)
        self.type = QtWidgets.QComboBox()
        self.type.addItems(self._sumtypes)
        self.range = RegionSelectWidget(self, dim, check=True)
        self.range.stateChanged.connect(self.dimensionChanged)
        lv = QtWidgets.QVBoxLayout()
        lv.addWidget(self.type)
        lv.addLayout(self.range)
        self.setLayout(lv)

    def getParameters(self):
        res = []
        for r, c in zip(self.range.getRegion(), self.range.getChecked()):
            if c:
                res.append(r)
            else:
                res.append([0, 0])
        return {"range": res, "sumtype": self.type.currentText()}

    def setParameters(self, range, sumtype):
        self.type.setCurrentIndex(self._sumtypes.index(sumtype))
        checked = []
        for i, r in enumerate(range):
            self.range.setRegion(i, r)
            checked.append(not (r[0] == 0 and r[1] == 0))
        self.range.setChecked(checked)


@filterGUI(IntegralCircleFilter)
class _CircleSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self.axes = [AxisSelectionLayout("Axis1", dim=dim, init=0), AxisSelectionLayout("Axis2", dim=dim, init=1)]
        self.center = [ScientificSpinBox(), ScientificSpinBox()]
        self.radiuses = [ScientificSpinBox(), ScientificSpinBox()]
        l0 = QtWidgets.QGridLayout()
        l0.addWidget(QtWidgets.QLabel("Center1"), 0, 0)
        l0.addWidget(self.center[0], 1, 0)
        l0.addWidget(QtWidgets.QLabel("Center2"), 0, 1)
        l0.addWidget(self.center[1], 1, 1)
        l0.addWidget(QtWidgets.QLabel("R"), 0, 2)
        l0.addWidget(self.radiuses[0], 1, 2)
        l0.addWidget(QtWidgets.QLabel("dr"), 0, 3)
        l0.addWidget(self.radiuses[1], 1, 3)
        l0.addWidget(QtWidgets.QPushButton("Load from freeline", clicked=self._LoadFromFreeLine), 1, 4)
        lh = QtWidgets.QVBoxLayout()
        lh.addLayout(self.axes[0])
        lh.addLayout(self.axes[1])
        lh.addLayout(l0)
        self.setLayout(lh)

    def getParameters(self):
        return {"center": [c.value() for c in self.center], "radiuses": [c.value() for c in self.radiuses], "axes": [c.getAxis() for c in self.axes]}

    def setParameters(self, center, radiuses, axes):
        for c, i in zip(self.center, center):
            c.setValue(i)
        for c, i in zip(self.radiuses, radiuses):
            c.setValue(i)
        for c, i in zip(self.axes, axes):
            c.setAxis(i)

    def _LoadFromFreeLine(self):
        c = frontCanvas()
        lines = c.getLineAnnotations()
        if len(lines) == 0:
            return
        line = lines[0]
        pos = np.array(line.getPosition())
        for c, i in zip(self.center, pos[0]):
            c.setValue(i)
        r = np.linalg.norm(pos[0] - pos[1])
        self.radiuses[0].setValue(r)
        self.radiuses[1].setValue(r / 100)


addFilter(IntegralFilter, gui=_IntegralSetting, guiName="Range", guiGroup="Sum, Mean, Median, ...")
addFilter(IntegralAllFilter, gui=_IntegralAllSetting, guiName="Axis", guiGroup="Sum, Mean, Median, ...")
addFilter(IntegralCircleFilter, gui=_CircleSetting, guiName="Circle", guiGroup="Sum, Mean, Median, ...")
