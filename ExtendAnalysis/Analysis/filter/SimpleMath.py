import numpy as np
import dask.array as da
from ExtendAnalysis import Wave, DaskWave
from .FilterInterface import FilterInterface


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


class ComplexFilter(FilterInterface):
    def __init__(self, type):
        self._type = type

    def _execute(self, wave, **kwargs):
        if self._type == "absolute":
            if isinstance(wave, Wave):
                wave.data = np.absoluste(wave.data)
            if isinstance(wave, DaskWave):
                wave.data = da.absolute(wave.data)
        if self._type == "real":
            if isinstance(wave, Wave):
                wave.data = np.real(wave.data)
            if isinstance(wave, DaskWave):
                wave.data = da.real(wave.data)
        if self._type == "imag":
            if isinstance(wave, Wave):
                wave.data = np.imag(wave.data)
            if isinstance(wave, DaskWave):
                wave.data = da.imag(wave.data)
        return wave
