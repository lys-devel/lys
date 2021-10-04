import numpy as np
import dask.array as da
from scipy import ndimage
from lys import DaskWave
from .FilterInterface import FilterInterface


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
