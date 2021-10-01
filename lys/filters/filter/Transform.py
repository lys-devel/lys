import numpy as np
import dask.array as da
import cv2
from scipy import ndimage
from lys import Wave, DaskWave
from .FilterInterface import FilterInterface


class SetAxisFilter(FilterInterface):
    def __init__(self, axis, val1, val2, type):
        self._axis = axis
        self._val1 = val1
        self._val2 = val2
        self._type = type

    def _execute(self, wave, **kwargs):
        if self._type == 'step':
            a = np.linspace(self._val1, self._val1 + self._val2 *
                            (wave.data.shape[self._axis] - 1), wave.data.shape[self._axis])
        else:
            a = np.linspace(self._val1, self._val1 + self._val2,
                            wave.data.shape[self._axis])
        wave.axes[self._axis] = a
        return wave

    def getParams(self):
        return self._axis, self._val1, self._val2, self._type


class AxisShiftFilter(FilterInterface):
    def __init__(self, shift, axes):
        self._shift = shift
        self._axes = axes

    def _execute(self, wave, **kwargs):
        for s, ax in zip(self._shift, self._axes):
            wave.axes[ax] = wave.getAxis(ax) + s
        return wave

    def getParams(self):
        return self._shift, self._axes


class MagnificationFilter(FilterInterface):
    def __init__(self, shift, axes):
        self._shift = shift
        self._axes = axes

    def _execute(self, wave, **kwargs):
        for s, ax in zip(self._shift, self._axes):
            tmp = wave.getAxis(ax)
            start = tmp[0]
            tmp = tmp - start
            tmp = tmp * s
            tmp = tmp + start
            wave.axes[ax] = tmp
        return wave

    def getParams(self):
        return self._shift, self._axes


class Rotation2DFilter(FilterInterface):
    def __init__(self, angle):
        self._angle = angle

    def _execute(self, wave, **kwargs):
        wave.data = ndimage.rotate(wave.data, self._angle, reshape=False)
        return wave

    def getParams(self):
        return self._angle


class SymmetrizeFilter(FilterInterface):
    def __init__(self, rotation, center, axes):
        self._rotation = int(rotation)
        self._center = center
        self._axes = np.array(axes)

    def _execute(self, wave, **kwargs):
        if isinstance(wave, Wave):
            return self._execute_wave(wave)  # TODO
        if isinstance(wave, DaskWave):
            return self._execute_dask(wave)
        return wave

    def _execute_dask(self, wave):
        gumap = da.gufunc(_symmetrze, signature="(i,j),(),(m)->(i,j)",
                          output_dtypes=wave.data.dtype, vectorize=True, axes=[tuple(self._axes), (), (0,), tuple(self._axes)], allow_rechunk=True)
        wave.data = gumap(wave.data, self._rotation, np.array(self._center))
        return wave

    def getParams(self):
        return str(self._rotation), self._center, self._axes


def _symmetrze(data, rotation, center):
    if len(data) <= 2:
        return np.empty((1,))
    s = data.shape
    dx = s[0] / 2 - center[0]
    dy = s[1] / 2 - center[1]
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


def _symmetrze2(data, rotation, center):
    if len(data) <= 2:
        return np.empty((1,))
    s = data.shape
    dx = s[0] / 2 - center[0]
    dy = s[1] / 2 - center[1]
    tmp = ndimage.shift(data, [dx, dy], cval=np.NaN)
    mask = np.array(tmp)
    mask[mask != np.nan] = 1
    mask = np.nan_to_num(mask, nan=0)
    tmp = np.nan_to_num(tmp, nan=0)
    rot = rotation
    d = np.array(tmp)
    m = np.array(mask)
    for i in range(1, rot):
        d = d + ndimage.rotate(tmp, 360 / rot * i, reshape=False)
        m = m + ndimage.rotate(mask, 360 / rot * i, reshape=False)
    mask = m
    #mask[mask < 1] = 1
    tmp = m
    tmp[m == 0] = np.nan


def _symmetrze3(data, rotation, center):
    if len(data) <= 2:
        return np.empty((1,))
    s = data.shape
    dx = s[0] / 2 - center[0]
    dy = s[1] / 2 - center[1]
    tmp = ndimage.shift(data, [dx, dy], cval=np.NaN)
    dlis = np.array([ndimage.rotate(tmp, 360 / rotation * i, reshape=False, order=1, cval=np.nan) for i in range(rotation)])
    sum = np.nan_to_num(dlis, nan=0).sum(axis=0)
    mask = np.where(np.isnan(dlis), 0, 1).sum(axis=0)
    mask[mask == 0] = 1
    return ndimage.shift(sum / mask, [-dx, -dy], cval=np.NaN)
