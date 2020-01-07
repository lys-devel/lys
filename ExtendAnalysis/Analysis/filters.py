import numpy as np
import scipy
import itertools
from scipy import signal
from scipy.ndimage import filters
from scipy.ndimage.interpolation import rotate
from scipy.interpolate import interpn
import cv2

import _pickle as cPickle

from dask_image import ndfilters as dfilters
from dask.array import apply_along_axis, einsum, fft, absolute, real, imag, flip, roll, angle

from ExtendAnalysis import Wave, tasks, task
from .MultiCut import DaskWave


class FilterInterface(object):
    def execute(self, wave, **kwargs):
        if isinstance(wave, Wave) or isinstance(wave, DaskWave) or isinstance(wave, np.array):
            self._execute(wave, **kwargs)
        if hasattr(wave, "__iter__"):
            for w in wave:
                self.execute(w, **kwargs)

    def _execute(self, wave, **kwargs):
        pass


class ShiftFilter(FilterInterface):
    def __init__(self, shift=None):
        self._s = shift

    def _execute(self, wave, shift=None, **kwargs):
        if shift is None:
            wave.data = (scipy.ndimage.interpolation.shift(np.array(wave.data, dtype=np.float32), self._s, cval=0))
        else:
            wave.data = (scipy.ndimage.interpolation.shift(np.array(wave.data, dtype=np.float32), shift, cval=0))


class SimpleMathFilter(FilterInterface):
    def __init__(self, type, value):
        self._type = type
        self._value = value

    def _execute(self, wave, **kwargs):
        if self._type == "+":
            wave.data = wave.data + self._value
        if self._type == "-":
            wave.data = wave.data - self._value
        if self._type == "*":
            wave.data = wave.data * self._value
        if self._type == "/":
            wave.data = wave.data / self._value
        if self._type == "**":
            wave.data = wave.data ** self._value
        return wave


class InterpFilter(FilterInterface):
    def __init__(self, size):
        self._size = size

    def _execute(self, wave, **kwargs):
        if isinstance(wave, Wave):
            size = self._size
            for i in range(len(size)):
                if size[i] == 0:
                    size[i] = len(wave.axes[i])
            axes_new = [np.linspace(min(wave.axes[i]), max(wave.axes[i]), size[i]) for i in range(len(self._size))]
            wave.data = interpn(wave.axes, wave.data, np.array(np.meshgrid(*axes_new)).T)
            wave.axes = axes_new
        if isinstance(wave, DaskWave):
            raise NotImplementedError()
        return wave


class MedianFilter(FilterInterface):
    def __init__(self, kernel):
        self._kernel = [int((k + 1) / 2) for k in kernel]

    def _execute(self, wave, **kwargs):
        if isinstance(wave, Wave):
            wave.data = filters.median_filter(wave.data, size=self._kernel)
            return wave
        if isinstance(wave, DaskWave):
            wave.data = dfilters.median_filter(wave.data, size=self._kernel)
            return wave
        return filters.median_filter(wave, size=self._kernel)

    def getKernel(self):
        return [int(2 * k - 1) for k in self._kernel]


class AverageFilter(FilterInterface):
    def __init__(self, kernel):
        self._kernel = [int((k + 1) / 2) for k in kernel]

    def _execute(self, wave, **kwargs):
        if isinstance(wave, Wave):
            wave.data = filters.uniform_filter(wave.data, size=self._kernel)
            return wave
        if isinstance(wave, DaskWave):
            wave.data = dfilters.uniform_filter(wave.data, size=self._kernel)
            return wave
        return filters.uniform_filter(wave, size=self._kernel)

    def getKernel(self):
        return [int(2 * k - 1) for k in self._kernel]


class GaussianFilter(FilterInterface):
    def __init__(self, kernel):
        self._kernel = kernel

    def _execute(self, wave, **kwargs):
        if isinstance(wave, Wave):
            wave.data = filters.gaussian_filter(wave.data, sigma=self._kernel)
            return wave
        if isinstance(wave, DaskWave):
            wave.data = dfilters.gaussian_filter(wave.data, sigma=self._kernel)
            return wave
        return filters.gaussian_filter(wave, sigma=self._kernel)

    def getKernel(self):
        return self._kernel


class BilateralFilter(FilterInterface):
    def __init__(self, kernel, s_color, s_space):
        self._kernel = kernel
        self._sc = s_color
        self._ss = s_space

    def _execute(self, wave, **kwargs):
        wave.data = cv2.bilateralFilter(np.array(wave.data, dtype=np.float32), self._kernel, self._sc, self._ss)


class ConvolutionFilter(FilterInterface):
    def __init__(self, axes):
        self._axes = axes

    def makeCore(self, dim):
        core = np.zeros([3 for i in range(dim)])
        core[tuple([1 for i in range(dim)])] = 1
        return core

    def _getKernel(self, core, axis):
        raise NotImplementedError()

    def _kernel(self, wave, axis):
        core = self.makeCore(self._getDim(wave))
        return self._getKernel(core, axis)

    def _getDim(self, wave):
        if isinstance(wave, np.ndarray):
            return wave.ndim
        else:
            return wave.data.ndim

    def _execute(self, wave, **kwargs):
        for ax in self._axes:
            kernel = self._kernel(wave, ax)
            if isinstance(wave, Wave):
                wave.data = filters.convolve(wave.data, kernel)
            if isinstance(wave, DaskWave):
                wave.data = dfilters.convolve(wave.data, kernel)
            else:
                wave = filters.convolve(wave, kernel)
        return wave

    def getAxes(self):
        return self._axes


class PrewittFilter(ConvolutionFilter):
    def _getKernel(self, core, axis):
        return filters.prewitt(core, axis=axis)


class SobelFilter(ConvolutionFilter):
    def _getKernel(self, core, axis):
        return filters.sobel(core, axis=axis)


class LaplacianFilter(ConvolutionFilter):
    def _getKernel(self, core, axis):
        res = np.array(core)
        for ax in self._axes:
            res += filters.convolve1d(core, [1, -2, 1], axis=ax)
        res[tuple([1 for i in range(core.ndim)])] -= 1
        return res

    def _execute(self, wave, **kwargs):
        kernel = self._kernel(wave, None)
        if isinstance(wave, Wave):
            wave.data = filters.convolve(wave.data, kernel)
        if isinstance(wave, DaskWave):
            wave.data = dfilters.convolve(wave.data, kernel)
        else:
            wave = filters.convolve(wave, kernel)
        return wave


class SharpenFilter(LaplacianFilter):
    def _getKernel(self, core, axis):
        res = super()._getKernel(core, axis)
        res[tuple([1 for i in range(core.ndim)])] -= 1
        return res


def _filt(wave, axes, b, a):
    if isinstance(wave, Wave):
        wave.data = np.array(wave.data, dtype=np.float32)
        for i in axes:
            wave.data = signal.filtfilt(b, a, wave.data, axis=i)
    if isinstance(wave, DaskWave):
        for i in axes:
            wave.data = apply_along_axis(_filts, i, wave.data, b=b, a=a)
    else:
        wave = signal.filtfilt(b, a, wave, axis=i)
    return wave


def _filts(x, b, a):
    if x.shape[0] != 1:
        return signal.filtfilt(b, a, x)
    else:
        return np.array([0])  # signal.filtfilt(b,a,x)


class LowPassFilter(FilterInterface):
    def __init__(self, order, cutoff, axes):
        self._b, self._a = signal.butter(order, cutoff)
        self._order = order
        self._cutoff = cutoff
        self._axes = axes

    def _execute(self, wave, **kwargs):
        return _filt(wave, self._axes, self._b, self._a)

    def getParams(self):
        return self._order, self._cutoff, self._axes


class HighPassFilter(FilterInterface):
    def __init__(self, order, cutoff, axes):
        self._b, self._a = signal.butter(order, cutoff, btype='highpass')
        self._order = order
        self._cutoff = cutoff
        self._axes = axes

    def _execute(self, wave, **kwargs):
        return _filt(wave, self._axes, self._b, self._a)

    def getParams(self):
        return self._order, self._cutoff, self._axes


class BandPassFilter(FilterInterface):
    def __init__(self, order, cutoff, axes):
        self._b, self._a = signal.butter(order, cutoff, btype='bandpass')
        self._order = order
        self._cutoff = cutoff
        self._axes = axes

    def _execute(self, wave, **kwargs):
        return _filt(wave, self._axes, self._b, self._a)

    def getParams(self):
        return self._order, self._cutoff, self._axes


class BandStopFilter(FilterInterface):
    def __init__(self, order, cutoff, axes):
        self._b, self._a = signal.butter(order, cutoff, btype='bandstop')
        self._order = order
        self._cutoff = cutoff
        self._axes = axes

    def _execute(self, wave, **kwargs):
        return _filt(wave, self._axes, self._b, self._a)

    def getParams(self):
        return self._order, self._cutoff, self._axes


class FourierFilter(FilterInterface):
    def __init__(self, axes, type="forward", process="absolute"):
        self.type = type
        self.axes = axes
        self.process = process

    def _execute(self, wave, **kwargs):
        for ax in self.axes:
            a = wave.axes[ax]
            if a is None or (a == np.array(None)).all():
                wave.axes[ax] = np.array(None)
            else:
                wave.axes[ax] = np.linspace(0, len(a) / (np.max(a) - np.min(a)), len(a))
        if isinstance(wave, Wave):
            if self.process == "absolute":
                func = np.absolute
            elif self.process == "real":
                func = np.real
            elif self.process == "imag":
                func = np.imag
            elif self.process == "phase":
                func = np.angle
            if self.type == "forward":
                wave.data = func(np.fft.fftn(wave.data, axes=self.axes))
            else:
                wave.data = func(np.fft.ifftn(wave.data, axes=self.axes))
        if isinstance(wave, DaskWave):
            if self.process == "absolute":
                func = absolute
            elif self.process == "real":
                func = real
            elif self.process == "imag":
                func = imag
            elif self.process == "phase":
                func = angle
            if self.type == "forward":
                wave.data = func(fft.fftn(wave.data, axes=self.axes))
            else:
                wave.data = func(fft.ifftn(wave.data, axes=self.axes))
        return wave

    def getParams(self):
        return self.axes, self.type, self.process


class ReverseFilter(FilterInterface):
    def __init__(self, axes):
        self.axes = axes

    def _execute(self, wave, **kwargs):
        for a in self.axes:
            if isinstance(wave, Wave):
                wave.data = np.flip(wave.data, a)
            else:
                wave.data = flip(wave.data, a)
        return wave

    def getAxes(self):
        return self.axes


class RollFilter(FilterInterface):
    def __init__(self, amount, axes):
        self.axes = axes
        self.amount = amount

    def _execute(self, wave, **kwargs):
        for a in self.axes:
            if self.amount == "1/2":
                amount = wave.data.shape[a] / 2
            if self.amount == "1/4":
                amount = wave.data.shape[a] / 4
            if self.amount == "-1/4":
                amount = -wave.data.shape[a] / 4
            if isinstance(wave, Wave):
                wave.data = np.roll(wave.data, amount, axis=a)
            else:
                wave.data = roll(wave.data, amount, axis=a)
        return wave

    def getParams(self):
        return self.amount, self.axes


class ReduceSizeFilter(FilterInterface):
    def __init__(self, kernel):
        self.kernel = kernel

    def _execute(self, wave, **kwargs):
        axes = []
        for i, k in enumerate(self.kernel):
            a = wave.axes[i]
            if (a == np.array(None)).all():
                axes.append(a)
            else:
                axes.append(wave.axes[i][0::k])
        res = None
        rans = [range(k) for k in self.kernel]
        for list in itertools.product(*rans):
            sl = tuple([slice(x, None, step) for x, step in zip(list, self.kernel)])
            if res is None:
                res = wave.data[sl]
            else:
                res += wave.data[sl]
        wave.data = res
        wave.axes = axes
        return wave

    def getKernel(self):
        return self.kernel


class NormalizeFilter(FilterInterface):
    def _makeSlice(self):
        sl = []
        for i, r in enumerate(self._range):
            if (r[0] == 0 and r[1] == 0) or self._axis == i:
                sl.append(slice(None))
            else:
                sl.append(slice(*r))
        return tuple(sl)

    def __init__(self, range, axis):
        self._range = range
        self._axis = axis

    def _execute(self, wave, **kwargs):
        axes = list(range(wave.data.ndim))
        if self._axis == -1:
            wave.data = wave.data / wave.data[self._makeSlice()].mean()
        else:
            letters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n"]
            axes.remove(self._axis)
            nor = 1 / wave.data[self._makeSlice()].mean(axis=axes)
            subscripts = ""
            for i in range(wave.data.ndim):
                subscripts += letters[i]
            subscripts = subscripts + "," + letters[self._axis] + "->" + subscripts
            wave.data = einsum(subscripts, wave.data, nor)

    def getParams(self):
        return self._range, self._axis


class SelectRegionFilter(FilterInterface):
    def __init__(self, range):
        self._range = range

    def _execute(self, wave, **kwargs):
        sl = []
        for r in self._range:
            if r[0] == 0 and r[1] == 0:
                sl.append(slice(None))
            else:
                sl.append(slice(*r))
        key = tuple(sl)
        wave.data = wave.data[key]
        wave.axes = [ax[s] for s, ax in zip(key, wave.axes)]
        return wave

    def getRegion(self):
        return self._range


"""
class SymmetrizationFilter(FilterInterface):
    #position=(x,y)
    def __init__(self,position,angle):
        self._pos=position
        self._ang=angle
    def _execute(self,wave,**kwargs):
        rotated=rotate(wave.data,self._ang)
        p_orig = np.array([pos[0]-(wave.data.shape[1]-1)/2,pos[1]-(wave.data.shape[0]-1)/2])
        c_rot = np.array([rotated.shape[0]-1)/2, (rotated.shape[1]-1)/2])
        t=self._ang/180*np.pi
        R=np.array([[np.cos(t),-np.sin(t)],[np.sin(t),np.cos(t)]])
        p_rot=c_rot+R*p_orig
        w=Wave()
        w.data=rotated
        return w
"""


class Filters(object):
    def __init__(self, filters):
        self._filters = []
        self._filters.extend(filters)

    def execute(self, wave, **kwargs):
        for f in self._filters:
            f.execute(wave, **kwargs)

    def insert(self, index, obj):
        self._filters.insert(index, obj)

    def getFilters(self):
        return self._filters

    def __str__(self):
        return str(cPickle.dumps(self))

    @staticmethod
    def fromString(str):
        return cPickle.loads(eval(str))
