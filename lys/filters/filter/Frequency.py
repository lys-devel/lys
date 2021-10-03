import numpy as np
import dask.array as da
from scipy import signal
from dask.array import apply_along_axis

from lys import DaskWave
from .FilterInterface import FilterInterface


def _filt(wave, axes, b, a):
    data = wave.data
    for i in axes:
        data = apply_along_axis(lambda x, b, a: signal.filtfilt(b, a, x), i, data, b, a, dtype=data.dtype, shape=(data.shape[i],))
    return DaskWave(data, *wave.axes, **wave.note)


class LowPassFilter(FilterInterface):
    """
    Apply low-pass (butterworth) filter by scipy.signal.filtfilt.

    Args:
        order(int): order of butterworth filter.
        cutoff(float): cutoff frequency in the Nyquist frequency unit (0 < cutoff < 1).
        axes: axes to be applied.

    """

    def __init__(self, order, cutoff, axes):
        self._b, self._a = signal.butter(order, cutoff)
        self._order = order
        self._cutoff = cutoff
        self._axes = axes

    def _execute(self, wave, *axes, **kwargs):
        return _filt(wave, self._axes, self._b, self._a)

    def getParameters(self):
        return {"order": self._order, "cutoff": self._cutoff, "axes": self._axes}


class HighPassFilter(FilterInterface):
    """
    Apply high-pass (butterworth) filter by scipy.signal.filtfilt.

    Args:
        order(int): order of butterworth filter.
        cutoff(float): cutoff frequency in the Nyquist frequency unit (0 < cutoff < 1).
        axes: axes to be applied.

    """

    def __init__(self, order, cutoff, axes):
        self._b, self._a = signal.butter(order, cutoff, btype='highpass')
        self._order = order
        self._cutoff = cutoff
        self._axes = axes

    def _execute(self, wave, **kwargs):
        return _filt(wave, self._axes, self._b, self._a)

    def getParameters(self):
        return {"order": self._order, "cutoff": self._cutoff, "axes": self._axes}


class BandPassFilter(FilterInterface):
    """
    Apply band-pass (butterworth) filter by scipy.signal.filtfilt.

    Args:
        order(int): order of butterworth filter.
        cutoff(length-2 sequence): cutoff frequency in the Nyquist frequency unit (0 < cutoff < 1).
        axes: axes to be applied.

    """

    def __init__(self, order, cutoff, axes):
        self._b, self._a = signal.butter(order, cutoff, btype='bandpass')
        self._order = order
        self._cutoff = cutoff
        self._axes = axes

    def _execute(self, wave, **kwargs):
        return _filt(wave, self._axes, self._b, self._a)

    def getParameters(self):
        return {"order": self._order, "cutoff": self._cutoff, "axes": self._axes}


class BandStopFilter(FilterInterface):
    """
    Apply band-stop (butterworth) filter by scipy.signal.filtfilt.

    Args:
        order(int): order of butterworth filter.
        cutoff(length-2 sequence): cutoff frequency in the Nyquist frequency unit (0 < cutoff < 1).
        axes: axes to be applied.

    """

    def __init__(self, order, cutoff, axes):
        self._b, self._a = signal.butter(order, cutoff, btype='bandstop')
        self._order = order
        self._cutoff = cutoff
        self._axes = axes

    def _execute(self, wave, **kwargs):
        return _filt(wave, self._axes, self._b, self._a)

    def getParameters(self):
        return {"order": self._order, "cutoff": self._cutoff, "axes": self._axes}


class FourierFilter(FilterInterface):
    """
    Apply fast Fourier transformation (FFT).

    If *process* is not complex, postprocessing is applied to FFT data.
    For example, when *process*="real", real part of FFT data is returned.

    Note:
        dask.array.fft requires chunk along *axes* along which the FFT is applied should be one.
        Uses should rechunk before applying this filter by :class:`RechunkFilter`.

    Args:
        axes(list of int): axes to be transformed
        type('forward' or 'backward'): specify foward or backward FFT.
        process('absolute' or 'real' or 'imag' or 'complex' or 'phase' or 'complex'): see description above.
        window('Rect' or 'Hann' or 'Hamming' or 'Blackman'): a window function used for FFT

    Examle:

        Apply FFT::

            w = Wave(np.ones([3, 3]))
            f = filters.FourierFilter(axes=[0, 1])
            result = f.execute(w)
            print(result.data)
            # [0,0,0], [0,9,0], [0,0,0]
            print(result.x)
            # [-0.75, 0, 0.75]

    """

    def __init__(self, axes, type="forward", process="absolute", window="Rect", roll=True):
        self.type = type
        self.axes = axes
        self.process = process
        self.window = window
        self.roll = roll

    def __getFunction(self, process):
        if process == "absolute":
            func = da.absolute
        elif process == "real":
            func = da.real
        elif process == "imag":
            func = da.imag
        elif process == "phase":
            func = da.angle
        elif process == 'complex':
            def func(x): return x
        return func

    def _execute(self, wave, *args, **kwargs):
        axes = self.__exeAxes(wave)
        size = [int(wave.data.shape[ax] / 2) for ax in self.axes]
        func = self.__getFunction(self.process)
        data = self.__applyWindow(wave)
        if self.type == "forward":
            data = func(da.fft.fftn(data, axes=tuple(self.axes)))
            if self.roll:
                data = da.roll(data, size, axis=tuple(self.axes))
        else:
            if self.roll:
                size_inv = [-s for s in size]
                data = da.roll(data, size_inv, axis=tuple(self.axes))
            data = func(da.fft.ifftn(data, axes=tuple(self.axes)))
        return DaskWave(data, *axes, **wave.note)

    def __exeAxes(self, wave):
        axes = []
        for ax in self.axes:
            a = wave.getAxis(ax)
            axis = np.linspace(0, len(a) / (np.max(a) - np.min(a)), len(a))
            if self.roll:
                axis = axis - axis[len(a) // 2]
            axes.append(axis)
        return axes

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

    def getParameters(self):
        return {"axes": self.axes, "type": self.type, "process": self.process, "window": self.window, "roll": self.roll}
