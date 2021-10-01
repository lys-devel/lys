import numpy as np
import dask.array as da
from scipy import signal
from dask.array import apply_along_axis

from lys import Wave, DaskWave
from .FilterInterface import FilterInterface


def _filt(wave, axes, b, a):
    if isinstance(wave, Wave):
        wave.data = np.array(wave.data, dtype=np.float32)
        for i in axes:
            wave.data = signal.filtfilt(b, a, wave.data, axis=i)
    elif isinstance(wave, DaskWave):
        for i in axes:
            wave.data = apply_along_axis(_filts, i, wave.data, b, a, dtype=wave.data.dtype, shape=(wave.data.shape[i],))
    else:
        wave = signal.filtfilt(b, a, wave, axis=i)
    return wave


def _filts(x, b, a):  # , dtype, shape):
    if x.shape[0] != 1:
        return signal.filtfilt(b, a, x)
    else:
        return np.empty(shape, dtype=dtype)


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
    def __init__(self, axes, type="forward", process="absolute", window=None, roll=True):
        self.type = type
        self.axes = axes
        self.process = process
        self.window = window
        self.roll = roll

    def __getLib(self, wave):
        if isinstance(wave, Wave):
            lib = np
        elif isinstance(wave, DaskWave):
            lib = da
        return lib

    def __getFunction(self, wave, process):
        lib = self.__getLib(wave)
        if process == "absolute":
            func = lib.absolute
        elif process == "real":
            func = lib.real
        elif process == "imag":
            func = lib.imag
        elif process == "phase":
            func = lib.angle
        elif process == 'complex':
            def func(x): return x
        return func

    def _execute(self, wave, **kwargs):
        self.__exeAxes(wave)
        size = [int(wave.data.shape[ax] / 2) for ax in self.axes]
        lib = self.__getLib(wave)
        func = self.__getFunction(wave, self.process)
        data = self.__applyWindow(wave)
        if self.type == "forward":
            wave.data = func(lib.fft.fftn(data, axes=tuple(self.axes)))
            if self.roll:
                wave.data = lib.roll(wave.data, size, axis=tuple(self.axes))
        else:
            if self.roll:
                size_inv = [-s for s in size]
                wave.data = lib.roll(data, size_inv, axis=tuple(self.axes))
            wave.data = func(lib.fft.ifftn(wave.data, axes=tuple(self.axes)))
        return wave

    def __exeAxes(self, wave):
        for ax in self.axes:
            a = wave.axes[ax]
            if a is None or (a == np.array(None)).all():
                wave.axes[ax] = np.array(None)
            else:
                wave.axes[ax] = np.linspace(0, len(a) / (np.max(a) - np.min(a)), len(a))
                if self.roll:
                    wave.axes[ax] = wave.axes[ax] - wave.axes[ax][len(a) // 2]

    def __applyWindow(self, wave):
        windowFunc = {"Rect": None, "Hann": signal.hann, "Hamming": signal.hamming, "Blackman": signal.blackman}
        index = ["i", "j", "k", "l", "m", "n", "o", "p", "q", "r"]
        f = windowFunc[self.window]
        if f is None:
            return wave.data
        window = []
        fr, to = "", ""
        for ax in range(wave.data.ndim):
            if ax in self.axes:
                window.append(f(wave.data.shape[ax]))
            else:
                window.append(np.array([1]))
            fr += index[ax] + ","
            to += index[ax]
        window = np.einsum(fr[:len(fr) - 1] + "->" + to, *window)
        return wave.data * window

    def getParams(self):
        return self.axes, self.type, self.process, self.window
