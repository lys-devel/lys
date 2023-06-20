import numpy as np
import dask.array as da
from scipy import ndimage

from lys import DaskWave, frontCanvas
from lys.Qt import QtWidgets
from lys.filters import FilterInterface, FilterSettingBase, filterGUI, addFilter
from lys.widgets import ScientificSpinBox, AxisSelectionLayout


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
            a = np.linspace(self._val1, self._val2, wave.data.shape[self._axis])
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
    Symmetrize 2D data.

    Args:
        rotation(int): The image is *rotation*-fold symmetrized.
        center(length 2 sequence): The central position of rotation.
        axes(length 2 sequence): The axes to be symmetrized.
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
    tmp = ndimage.shift(data, [dx, dy], cval=np.NaN, order=1)
    mask = np.where(np.isnan(tmp), 0, 1)
    tmp[np.isnan(tmp)] = 0
    dlis = np.array([ndimage.rotate(tmp, 360 / rotation * i, reshape=False, cval=0, order=1) for i in range(rotation)])
    mlis = np.array([ndimage.rotate(mask, 360 / rotation * i, reshape=False, cval=0, order=1) for i in range(rotation)])
    sum = dlis.sum(axis=0)
    m_sum = mlis.sum(axis=0)
    sum[m_sum < 1] = np.nan
    m_sum[m_sum < 1] = 1

    return ndimage.shift(sum / m_sum, [-dx, -dy], cval=np.NaN, order=1)


class OffsetFilter(FilterInterface):
    """
    Add offset to data.

    Args:
        offset(list): The offset added for each axes.
    """

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


class MirrorFilter(FilterInterface):
    """
    Reflect 2D data with respect to a line.

    Args:
        positions(2*2 array): The positions that specify mirror axis in the form of [(x1, y1), (x2, y2)].
        axes(length 2 sequence): The axes to be symmetrized.
        sum(bool): If sum is False, the image is reflected with respect to the mirror axis. Otherwise, the mirrored image is added to the original image.
    """

    def __init__(self, positions, axes=(0, 1), sum=True):
        self._pos = np.array(positions)
        self._axes = axes
        self._sum = sum

    def _calcPosition(self, x0, y0, a, b, c):
        x1 = (-a**2 * x0 - 2 * a * b * y0 - 2 * a * c + b**2 * x0) / (a**2 + b**2)
        y1 = (a**2 * y0 - 2 * a * b * x0 - b**2 * y0 - 2 * b * c) / (a**2 + b**2)
        return x1, y1

    def _calcCoords(self, wave):
        x, y = wave.getAxis(self._axes[0]), wave.getAxis(self._axes[1])
        dx, dy = (x[-1] - x[0]) / (len(x) - 1), (y[-1] - y[0]) / (len(y) - 1)
        pos = [[(self._pos[i][0] - x[0]) / dx, (self._pos[i][1] - y[0]) / dy] for i in range(2)]
        a, b, c = pos[1][1] - pos[0][1], -pos[1][0] + pos[0][0], pos[1][0] * pos[0][1] - pos[1][1] * pos[0][0]

        xy = np.arange(wave.data.shape[self._axes[0]]), np.arange(wave.data.shape[self._axes[0]])
        xy = np.array(np.meshgrid(*xy)).transpose(1, 2, 0)
        xy = np.array([[self._calcPosition(x0, y0, a, b, c) for x0, y0 in tmp] for tmp in xy]).transpose(2, 1, 0)
        return xy

    def _execute(self, wave, *args, **kwargs):
        coords = self._calcCoords(wave)

        def _mirror(data):
            if len(data) <= 2:
                return np.empty((1,))
            mir = ndimage.map_coordinates(data, coords, cval=np.nan, order=1)
            if self._sum:
                norm = np.where(np.isnan(data), 0, 1) + np.where(np.isnan(mir), 0, 1)
                norm[norm == 0] = 1
                return (np.nan_to_num(data) + np.nan_to_num(mir)) / norm
            else:
                return mir

        gumap = da.gufunc(_mirror, signature="(i,j)->(i,j)", output_dtypes=float, vectorize=True, axes=[tuple(self._axes), tuple(self._axes)], allow_rechunk=True)
        data = gumap(wave.data)
        return DaskWave(data, *wave.axes, **wave.note)

    def getParameters(self):
        return {"positions": self._pos.tolist(), "axes": self._axes, "sum": self._sum}


@filterGUI(SetAxisFilter)
class _SetAxisSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = QtWidgets.QGridLayout()
        self._axis = QtWidgets.QComboBox()
        for i in range(dimension):
            self._axis.addItem("Axis" + str(i + 1))
        self._type = QtWidgets.QComboBox()
        self._type.addItem("Start & Stop")
        self._type.addItem("Start & Step")
        self._val1 = ScientificSpinBox()
        self._val2 = ScientificSpinBox()
        self._val2.setValue(1)
        self._layout.addWidget(QtWidgets.QLabel('Axis'), 0, 0)
        self._layout.addWidget(QtWidgets.QLabel('Type'), 0, 1)
        self._layout.addWidget(QtWidgets.QLabel('Start'), 0, 2)
        self._layout.addWidget(QtWidgets.QLabel('Stop/Step'), 0, 3)
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
        self._layout = QtWidgets.QGridLayout()
        self._dim = dimension
        self._values = []
        for i in range(dimension):
            wid = ScientificSpinBox()
            self._values.append(wid)
            self._layout.addWidget(QtWidgets.QLabel('Axis' + str(i + 1)), 0, i)
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
        self._layout = QtWidgets.QGridLayout()
        self._dim = dimension
        self._values = []
        for i in range(dimension):
            wid = ScientificSpinBox()
            wid.setValue(1)
            self._values.append(wid)
            self._layout.addWidget(QtWidgets.QLabel('Axis' + str(i + 1)), 0, i)
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
        self._layout = QtWidgets.QHBoxLayout()
        self._layout.addWidget(QtWidgets.QLabel('Rotation'))
        self._layout.addWidget(self._rot)

        self.axis1 = AxisSelectionLayout("Axis 1", self.dim, 0)
        self.axis2 = AxisSelectionLayout("Axis 2", self.dim, 1)

        lay = QtWidgets.QVBoxLayout()
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
        layout = QtWidgets.QHBoxLayout()
        self.axes = [AxisSelectionLayout("Axis1", dim=dim, init=0), AxisSelectionLayout("Axis2", dim=dim, init=1)]
        self._combo = QtWidgets.QComboBox()
        self._combo.addItems(["1", "2", "3", "4", "6"])
        l0 = QtWidgets.QGridLayout()
        self._center = [ScientificSpinBox(), ScientificSpinBox()]
        l0.addWidget(QtWidgets.QLabel("Symmetry (fold)"), 0, 0)
        l0.addWidget(self._combo, 1, 0)
        l0.addWidget(QtWidgets.QLabel("Center1"), 0, 1)
        l0.addWidget(self._center[0], 1, 1)
        l0.addWidget(QtWidgets.QLabel("Center2"), 0, 2)
        l0.addWidget(self._center[1], 1, 2)
        layout.addLayout(l0)
        lv = QtWidgets.QVBoxLayout()
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


@ filterGUI(MirrorFilter)
class _MirrorSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self.axes = [AxisSelectionLayout("Axis1", dim=dim, init=0), AxisSelectionLayout("Axis2", dim=dim, init=1)]
        self._combo = QtWidgets.QComboBox()
        self._combo.addItems(["Sum", "Mirror"])
        self._p1 = [ScientificSpinBox(), ScientificSpinBox()]
        self._p2 = [ScientificSpinBox(), ScientificSpinBox()]

        l0 = QtWidgets.QGridLayout()
        l0.addWidget(QtWidgets.QLabel("Position 1"), 0, 0)
        l0.addWidget(self._p1[0], 0, 1)
        l0.addWidget(self._p1[1], 0, 2)
        l0.addWidget(QtWidgets.QLabel("Position 2"), 1, 0)
        l0.addWidget(self._p2[0], 1, 1)
        l0.addWidget(self._p2[1], 1, 2)
        l0.addWidget(QtWidgets.QPushButton("From LineAnnot.", clicked=self.__load), 0, 3)
        l0.addWidget(QtWidgets.QLabel("Output"), 2, 0)
        l0.addWidget(self._combo, 2, 1, 1, 2)

        lv = QtWidgets.QVBoxLayout()
        lv.addLayout(self.axes[0])
        lv.addLayout(self.axes[1])
        lv.addLayout(l0)
        self.setLayout(lv)

    def __load(self):
        c = frontCanvas()
        lines = c.getLineAnnotations()
        if len(lines) == 0:
            QtWidgets.QMessageBox.information(self, "Warning", "No line annotation found on the front canvas.\nAdd line annotation by right click -> draw line.")
            return
        line = lines[0]
        p1, p2 = line.getPosition()
        self._p1[0].setValue(p1[0])
        self._p1[1].setValue(p1[1])
        self._p2[0].setValue(p2[0])
        self._p2[1].setValue(p2[1])

    def getParameters(self):
        pos = [[p.value() for p in self._p1], [p.value() for p in self._p2]]
        return {"positions": pos, "sum": self._combo.currentText() == "Sum", "axes": [c.getAxis() for c in self.axes]}

    def setParameters(self, positions, axes, sum):
        self._p1[0].setValue(positions[0][0])
        self._p1[1].setValue(positions[0][1])
        self._p2[0].setValue(positions[1][0])
        self._p2[1].setValue(positions[1][1])
        if sum:
            self._combo.setCurrentText("Sum")
        else:
            self._combo.setCurrentText("Mirror")
        for c, i in zip(self.axes, axes):
            c.setAxis(i)


addFilter(SetAxisFilter, gui=_SetAxisSetting, guiName="Set axis", guiGroup="Axis")
addFilter(AxisShiftFilter, gui=_ShiftSetting, guiName="Shift axis", guiGroup="Axis")
addFilter(MagnificationFilter, gui=_MagnificationSetting, guiName="Scale axis", guiGroup="Axis")
addFilter(OffsetFilter)

addFilter(Rotation2DFilter, gui=_Rotation2DSetting, guiName="Rotate image", guiGroup="Image transformation")
addFilter(SymmetrizeFilter, gui=_SymmetrizeSetting, guiName="Symmetrize", guiGroup="Symmetric operation")
addFilter(MirrorFilter, gui=_MirrorSetting, guiName="Mirror", guiGroup="Symmetric operation")
