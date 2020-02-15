import numpy as np
from scipy import signal
from dask.array import fft, absolute, real, imag, apply_along_axis

from ExtendAnalysis import Wave, DaskWave
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
