import numpy as np
import cv2

from . import FilterInterface


class SetAxisFilter(FilterInterface):
    def __init__(self, axis, val1, val2, type):
        self._axis = axis
        self._val1 = val1
        self._val2 = val2
        self._type = type

    def _execute(self, wave, **kwargs):
        if self._type == 'step':
            a = np.linspace(self._val1, self._val1+self._val2 * wave.data.shape[self._axis], wave.data.shape[self._axis])
        else:
            a = np.linspace(self._val1, self._val1+self._val2, wave.data.shape[self._axis])
        wave.axes[self._axis] = a
        return wave

    def getParams(self):
        return self._axis, self._val1, self._val2, self._type

class ShiftFilter(FilterInterface):
    def __init__(self, shift, axes):
        self._shift = shift
        self._axes=axes

    def _execute(self, wave, **kwargs):
        for s, ax in zip(self._shift, self._axes):
            wave.axes[ax] = wave.getAxis(ax) + s
        return wave

    def getParams(self):
        return self._shift, self._axes

class MagnificationFilter(FilterInterface):
    def __init__(self, shift, axes):
        self._shift = shift
        self._axes=axes

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
        w, h = wave.data.shape[0], wave.data.shape[1]
        R=cv2.getRotationMatrix2D((w / 2, h / 2), self._angle, 1)
        wave.data = cv2.warpAffine(wave.data, R, (w, h))
        return wave

    def getParams(self):
        return self._angle
