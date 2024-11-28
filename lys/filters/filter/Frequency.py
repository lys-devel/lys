import numpy as np
import dask.array as da
from scipy import signal
from dask.array import apply_along_axis

from lys import DaskWave, Version
from lys.Qt import QtWidgets
from lys.filters import FilterInterface, FilterSettingBase, filterGUI, addFilter
from lys.widgets import AxisCheckLayout


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
    For example, when *process* ="real", real part of FFT data is returned.

    Note:
        dask.array.fft requires chunk along *axes* along which the FFT is applied should be one.
        Uses should rechunk before applying this filter by :class:`RechunkFilter`.

    Args:
        axes(list of int): axes to be transformed
        type('forward' or 'backward'): specify foward or backward FFT.
        process('absolute' or 'real' or 'imag' or 'complex' or 'phase' or 'complex'): see description above.
        window('Rect' or 'Hann' or 'Hamming' or 'Blackman'): a window function used for FFT

    Examle::

        from lys import Wave, filters

        # prepare data and filter
        w = Wave(np.ones([3, 3]))
        f = filters.FourierFilter(axes=[0, 1])
        result = f.execute(w)

        # FFT changes x axis as well as data
        print(result.data) # [0,0,0], [0,9,0], [0,0,0]
        print(result.x)    # [-0.3333333, 0, 0.33333333]

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
            def func(x):
                return x
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
        for ax in range(wave.data.ndim):
            if ax in self.axes:
                a = wave.getAxis(ax)
                axis = np.fft.fftfreq(len(a), d=(np.max(a) - np.min(a)) / (len(a) - 1))
                if self.roll:
                    axis = np.roll(axis, len(a) // 2)
                axes.append(axis)
            else:
                axes.append(wave.axes[ax])
        return axes

    def __applyWindow(self, wave):
        if hasattr(signal, "windows"):
            windowFunc = {"Rect": None, "Hann": signal.windows.hann, "Hamming": signal.windows.hamming, "Blackman": signal.windows.blackman}
        else:
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


class _Setting1(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self._layout = QtWidgets.QHBoxLayout()
        self._cut = QtWidgets.QDoubleSpinBox()
        self._cut.setDecimals(3)
        self._cut.setRange(0, 1)
        self._cut.setValue(0.2)
        self._order = QtWidgets.QSpinBox()
        self._order.setRange(0, 1000)
        self._order.setValue(1)
        self._layout.addWidget(QtWidgets.QLabel('Order'))
        self._layout.addWidget(self._order)
        self._layout.addWidget(QtWidgets.QLabel('Cutoff'))
        self._layout.addWidget(self._cut)

        self._axes = AxisCheckLayout(dim)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(self._layout)
        vbox.addLayout(self._axes)
        self.setLayout(vbox)

    def getParameters(self):
        return {"order": self._order.value(), "cutoff": self._cut.value(), "axes": self._axes.GetChecked()}

    def setParameters(self, order, cutoff, axes):
        self._cut.setValue(cutoff)
        self._order.setValue(order)
        self._axes.SetChecked(axes)


@filterGUI(LowPassFilter)
class _LowPassSetting(_Setting1):
    pass


@filterGUI(HighPassFilter)
class _HighPassSetting(_Setting1):
    pass


class _Setting2(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self._layout = QtWidgets.QHBoxLayout()
        self._cut1 = QtWidgets.QDoubleSpinBox()
        self._cut1.setDecimals(3)
        self._cut1.setRange(0, 1)
        self._cut1.setValue(0.2)
        self._cut2 = QtWidgets.QDoubleSpinBox()
        self._cut2.setDecimals(3)
        self._cut2.setRange(0, 1)
        self._cut2.setValue(0.8)
        self._order = QtWidgets.QSpinBox()
        self._order.setRange(0, 1000)
        self._order.setValue(1)
        self._layout.addWidget(QtWidgets.QLabel('Order'))
        self._layout.addWidget(self._order)
        self._layout.addWidget(QtWidgets.QLabel('Low'))
        self._layout.addWidget(self._cut1)
        self._layout.addWidget(QtWidgets.QLabel('High'))
        self._layout.addWidget(self._cut2)
        self._axes = AxisCheckLayout(dim)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(self._layout)
        vbox.addLayout(self._axes)
        self.setLayout(vbox)

    def getParameters(self):
        return {"order": self._order.value(), "cutoff": [self._cut1.value(), self._cut2.value()], "axes": self._axes.GetChecked()}

    def setParameters(self, order, cutoff, axes):
        self._cut1.setValue(cutoff[0])
        self._cut2.setValue(cutoff[1])
        self._order.setValue(order)
        self._axes.SetChecked(axes)


@filterGUI(BandPassFilter)
class _BandPassSetting(_Setting2):
    pass


@filterGUI(BandStopFilter)
class _BandStopSetting(_Setting2):
    pass


@filterGUI(FourierFilter)
class _FourierSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self.dim = dim
        self._combo = QtWidgets.QComboBox()
        self._combo.addItem('forward', 'forward')
        self._combo.addItem('backward', 'backward')
        self._process = QtWidgets.QComboBox()
        self._process.addItem('absolute', 'absolute')
        self._process.addItem('real', 'real')
        self._process.addItem('imag', 'imag')
        self._process.addItem('phase', 'phase')
        self._process.addItem('complex', 'complex')
        self._window = QtWidgets.QComboBox()
        self._window.addItem("Rect", "Rect")
        self._window.addItem("Hann", "Hann")
        self._window.addItem("Hamming", "Hamming")
        self._window.addItem("Blackman", "Blackman")
        self._axes = AxisCheckLayout(dim)

        self._layout = QtWidgets.QGridLayout()
        self._layout.addWidget(QtWidgets.QLabel('Axes'), 0, 0)
        self._layout.addLayout(self._axes, 0, 1, 1, 2)
        self._layout.addWidget(QtWidgets.QLabel('Direction'), 1, 0)
        self._layout.addWidget(QtWidgets.QLabel('Process'), 1, 1)
        self._layout.addWidget(QtWidgets.QLabel('Window'), 1, 2)
        self._layout.addWidget(self._combo, 2, 0)
        self._layout.addWidget(self._process, 2, 1)
        self._layout.addWidget(self._window, 2, 2)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"axes": self._axes.GetChecked(), "type": self._combo.currentText(), "process": self._process.currentText(), "window": self._window.currentText(), "roll": True}

    def setParameters(self, axes, type, process, window, roll):
        self._axes.SetChecked(axes)
        self._process.setCurrentIndex(self._process.findData(process))
        self._combo.setCurrentIndex(self._combo.findData(type))
        self._window.setCurrentIndex(self._window.findData(window))


addFilter(LowPassFilter, gui=_LowPassSetting, guiName="Low pass filter", guiGroup="Frequency filter")
addFilter(HighPassFilter, gui=_HighPassSetting, guiName="High pass filter", guiGroup="Frequency filter")
addFilter(BandPassFilter, gui=_BandPassSetting, guiName="Band pass filter", guiGroup="Frequency filter")
addFilter(BandStopFilter, gui=_BandStopSetting, guiName="Band stop filter", guiGroup="Frequency filter")
addFilter(FourierFilter, gui=_FourierSetting, guiName="Fourier Transformation")
