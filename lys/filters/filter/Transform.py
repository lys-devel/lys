import numpy as np
import dask.array as da
from scipy import ndimage

from lys import DaskWave
from lys.filters import FilterSettingBase, filterGUI, addFilter

from .FilterInterface import FilterInterface
from .CommonWidgets import QGridLayout, QComboBox, ScientificSpinBox, QLabel, QHBoxLayout, QVBoxLayout, AxisSelectionLayout


class SetAxisFilter(FilterInterface):
    """
    Set axis value.

    When type='step', then the new axis is val1, val1 + val2, val1 + 2 * val2, ...
    When type='stop', then the new axis is val1, ..., val2.

    Args:
        axis(int): axis to be set.
        val1(float): see description above.
        val2(float): see description above.
        type('step' or 'stop'): see description above.
    """

    def __init__(self, axis, val1, val2, type):
        self._axis = axis
        self._val1 = val1
        self._val2 = val2
        self._type = type

    def _execute(self, wave, *args, **kwargs):
        if self._type == 'step':
            a = np.linspace(self._val1, self._val1 + self._val2 *
                            (wave.data.shape[self._axis] - 1), wave.data.shape[self._axis])
        else:
            a = np.linspace(self._val1, self._val1 + self._val2, wave.data.shape[self._axis])
        axes = list(wave.axes)
        axes[self._axis] = a
        return DaskWave(wave.data, *axes, **wave.note)

    def getParameters(self):
        return {"axis": self._axis, "val1": self._val1, "val2": self._val2, "type": self._type}


class AxisShiftFilter(FilterInterface):
    """
    Shit axes by *shift*

    Args:
        shift(list of float): The values to be added to the axes.
        axes(list of int): The shifted axes.
    """

    def __init__(self, shift, axes):
        self._shift = shift
        self._axes = axes

    def _execute(self, wave, *args, **kwargs):
        axes = list(wave.axes)
        for s, ax in zip(self._shift, self._axes):
            axes[ax] = wave.getAxis(ax) + s
        return DaskWave(wave.data, *axes, **wave.note)

    def getParameters(self):
        return {"shift": self._shift, "axes": self._axes}


class MagnificationFilter(FilterInterface):
    """
    Magnify axes by *mag*

    Args:
        shift(list of float): The values to be added to the axes.
        axes(list of int): The shifted axes.
    """

    def __init__(self, mag, axes):
        self._shift = mag
        self._axes = axes

    def _execute(self, wave, **kwargs):
        axes = list(wave.axes)
        for s, ax in zip(self._shift, self._axes):
            tmp = wave.getAxis(ax)
            start = tmp[0]
            tmp = tmp - start
            tmp = tmp * s
            tmp = tmp + start
            axes[ax] = tmp
        return DaskWave(wave.data, *axes, **wave.note)

    def getParameters(self):
        return {"mag": self._shift, "axes": self._axes}


class Rotation2DFilter(FilterInterface):
    """
    The array is rotated in the plane defined by the two axes given by the axes parameter using spline interpolation.

    Args:
        angle(float): The rotation angle in degrees
        axes:(tuple of 2 ints): The two axes that define the plane of rotation.
    """

    def __init__(self, angle, axes=(0, 1)):
        self._angle = angle
        self._axes = axes

    def _execute(self, wave, *args, **kwargs):
        def f(x):
            return ndimage.rotate(x, self._angle, reshape=False)
        gumap = da.gufunc(f, signature="(i,j)->(i,j)",
                          output_dtypes=wave.data.dtype, vectorize=True, axes=[tuple(self._axes), tuple(self._axes)], allow_rechunk=True)
        data = gumap(wave.data)
        return DaskWave(data, *wave.axes, **wave.note)

    def getParameters(self):
        if not hasattr(self, "_axes"):
            self._axes = (0, 1)
        return {"angle": self._angle, "axes": self._axes}


class SymmetrizeFilter(FilterInterface):
    """
    Symmetrize data.
    """

    def __init__(self, rotation, center, axes=(0, 1)):
        self._rotation = int(rotation)
        self._center = center
        self._axes = axes

    def _execute(self, wave, *args, **kwargs):
        return self._execute_dask(wave)

    def _execute_dask(self, wave):
        center = wave.posToPoint(self._center[0], self._axes[0]), wave.posToPoint(self._center[1], self._axes[1])
        gumap = da.gufunc(_symmetrze, signature="(i,j),(),(m)->(i,j)",
                          output_dtypes=float, vectorize=True, axes=[tuple(self._axes), (), (0,), tuple(self._axes)], allow_rechunk=True)
        data = gumap(wave.data.astype(float), self._rotation, np.array(center))
        return DaskWave(data, *wave.axes, **wave.note)

    def getParameters(self):
        return {"rotation": str(self._rotation), "center": self._center, "axes": self._axes}


def _symmetrze(data, rotation, center):
    if len(data) <= 2:
        return np.empty((1,))
    s = data.shape
    dx = (s[0] - 1) / 2 - center[0]
    dy = (s[1] - 1) / 2 - center[1]
    tmp = ndimage.shift(data, [dx, dy], cval=np.NaN, order=0)
    mask = np.where(np.isnan(tmp), 0, 1)
    tmp[np.isnan(tmp)] = 0
    dlis = np.array([ndimage.rotate(tmp, 360 / rotation * i, reshape=False, cval=0) for i in range(rotation)])
    mlis = np.array([ndimage.rotate(mask, 360 / rotation * i, reshape=False, cval=0) for i in range(rotation)])
    sum = dlis.sum(axis=0)
    m_sum = mlis.sum(axis=0)
    sum[m_sum < 1] = np.nan
    m_sum[m_sum < 1] = 1

    return ndimage.shift(sum / m_sum, [-dx, -dy], cval=np.NaN, order=0)


class OffsetFilter(FilterInterface):
    def __init__(self, offset):
        self._offset = offset

    def _execute(self, wave, *args, **kwargs):
        if wave.data.ndim == 1:
            xdata = np.array(wave.getAxis(0))
            ydata = wave.data
            if not self._offset[2] == 0.0:
                xdata = xdata * self._offset[2]
            if not self._offset[3] == 0.0:
                ydata = ydata * self._offset[3]
            xdata = xdata + self._offset[0]
            ydata = ydata + self._offset[1]
            return DaskWave(ydata, xdata, **wave.note)
        elif wave.data.ndim == 2 or wave.data.ndim == 3:
            xdata = np.array(wave.getAxis(0))
            ydata = np.array(wave.getAxis(1))
            if not self._offset[2] == 0.0:
                xdata = xdata * self._offset[2]
            if not self._offset[3] == 0.0:
                ydata = ydata * self._offset[3]
            xdata = xdata + self._offset[0]
            ydata = ydata + self._offset[1]
            return DaskWave(wave.data, xdata, ydata, **wave.note)

    def getParameters(self):
        return {"offset": self._offset}


@filterGUI(SetAxisFilter)
class _SetAxisSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = QGridLayout()
        self._axis = QComboBox()
        for i in range(dimension):
            self._axis.addItem("Axis" + str(i + 1))
        self._type = QComboBox()
        self._type.addItem("Start & Stop")
        self._type.addItem("Start & Step")
        self._val1 = ScientificSpinBox()
        self._val2 = ScientificSpinBox()
        self._val2.setValue(1)
        self._layout.addWidget(QLabel('Axis'), 0, 0)
        self._layout.addWidget(QLabel('Type'), 0, 1)
        self._layout.addWidget(QLabel('Start'), 0, 2)
        self._layout.addWidget(QLabel('Stop/Step'), 0, 3)
        self._layout.addWidget(self._axis, 1, 0)
        self._layout.addWidget(self._type, 1, 1)
        self._layout.addWidget(self._val1, 1, 2)
        self._layout.addWidget(self._val2, 1, 3)
        self.setLayout(self._layout)

    def getParameters(self):
        if self._type.currentIndex() == 0:
            type = "stop"
        else:
            type = "step"
        return {"axis": self._axis.currentIndex(), "val1": self._val1.value(), "val2": self._val2.value(), "type": type}

    def setParameters(self, axis, val1, val2, type):
        self._axis.setCurrentIndex(axis)
        if type == "stop":
            self._type.setCurrentIndex(0)
        else:
            self._type.setCurrentIndex(1)
        self._val1.setValue(val1)
        self._val2.setValue(val2)


@filterGUI(AxisShiftFilter)
class _ShiftSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = QGridLayout()
        self._dim = dimension
        self._values = []
        for i in range(dimension):
            wid = ScientificSpinBox()
            self._values.append(wid)
            self._layout.addWidget(QLabel('Axis' + str(i + 1)), 0, i)
            self._layout.addWidget(wid, 1, i)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"shift": [v.value() for v in self._values], "axes": list(range(self._dim))}

    def setParameters(self, shift, axes):
        for s, ax in zip(shift, axes):
            self._values[ax].setValue(s)


@filterGUI(MagnificationFilter)
class _MagnificationSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = QGridLayout()
        self._dim = dimension
        self._values = []
        for i in range(dimension):
            wid = ScientificSpinBox()
            wid.setValue(1)
            self._values.append(wid)
            self._layout.addWidget(QLabel('Axis' + str(i + 1)), 0, i)
            self._layout.addWidget(wid, 1, i)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"mag": [v.value() for v in self._values], "axes": list(range(self._dim))}

    def setParameters(self, mag, axes):
        for s, ax in zip(mag, axes):
            self._values[ax].setValue(s)


@filterGUI(Rotation2DFilter)
class _Rotation2DSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._rot = ScientificSpinBox()
        self._layout = QHBoxLayout()
        self._layout.addWidget(QLabel('Rotation'))
        self._layout.addWidget(self._rot)

        self.axis1 = AxisSelectionLayout("Axis 1", self.dim, 0)
        self.axis2 = AxisSelectionLayout("Axis 2", self.dim, 1)

        lay = QVBoxLayout()
        lay.addLayout(self._layout)
        lay.addLayout(self.axis1)
        lay.addLayout(self.axis2)
        self.setLayout(lay)

    def getParameters(self):
        return {"angle": self._rot.value(), "axes": (self.axis1.getAxis(), self.axis2.getAxis())}

    def setParameters(self, angle, axes):
        self._rot.setValue(angle)
        self.axis1.setAxis(axes[0])
        self.axis2.setAxis(axes[1])


@ filterGUI(SymmetrizeFilter)
class _SymmetrizeSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        layout = QHBoxLayout()
        self.axes = [AxisSelectionLayout("Axis1", dim=dim, init=0), AxisSelectionLayout("Axis2", dim=dim, init=1)]
        self._combo = QComboBox()
        self._combo.addItems(["1", "2", "3", "4", "6"])
        l0 = QGridLayout()
        self._center = [ScientificSpinBox(), ScientificSpinBox()]
        l0.addWidget(QLabel("Symmetry (fold)"), 0, 0)
        l0.addWidget(self._combo, 1, 0)
        l0.addWidget(QLabel("Center1"), 0, 1)
        l0.addWidget(self._center[0], 1, 1)
        l0.addWidget(QLabel("Center2"), 0, 2)
        l0.addWidget(self._center[1], 1, 2)
        layout.addLayout(l0)
        lv = QVBoxLayout()
        lv.addLayout(self.axes[0])
        lv.addLayout(self.axes[1])
        lv.addLayout(layout)
        self.setLayout(lv)

    def getParameters(self):
        return {"rotation": self._combo.currentText(), "center": [i.value() for i in self._center], "axes": [c.getAxis() for c in self.axes]}

    def setParameters(self, rotation, center, axes):
        self._center[0].setValue(center[0])
        self._center[1].setValue(center[1])
        self._combo.setCurrentText(rotation)
        for c, i in zip(self.axes, axes):
            c.setAxis(i)


addFilter(SetAxisFilter, gui=_SetAxisSetting, guiName="Set axis", guiGroup="Axis")
addFilter(AxisShiftFilter, gui=_ShiftSetting, guiName="Shift axis", guiGroup="Axis")
addFilter(MagnificationFilter, gui=_MagnificationSetting, guiName="Scale axis", guiGroup="Axis")
addFilter(OffsetFilter)

addFilter(Rotation2DFilter, gui=_Rotation2DSetting, guiName="Rotate image", guiGroup="Image transformation")
addFilter(SymmetrizeFilter, gui=_SymmetrizeSetting, guiName="Symmetrize", guiGroup="Symmetric operation")
