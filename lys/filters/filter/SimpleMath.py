import numpy as np
import dask.array as da
from lys import DaskWave
from .FilterInterface import FilterInterface


class SimpleMathFilter(FilterInterface):
    """
    Calculate data [+-*\] value.

    Args:
        type('+' or '-' or '*' or '/'): operator type.
        value(float): value used for calculation.
    """

    def __init__(self, type, value):
        self._type = type
        self._value = value

    def _execute(self, wave, *args, **kwargs):
        if self._type == "+":
            data = wave.data + self._value
        if self._type == "-":
            data = wave.data - self._value
        if self._type == "*":
            data = wave.data * self._value
        if self._type == "/":
            data = wave.data / self._value
        if self._type == "**":
            data = wave.data ** self._value
        return DaskWave(data, *wave.axes, **wave.note)

    def getParameters(self):
        return {"type": self._type, "value": self._value}


class ComplexFilter(FilterInterface):
    """
    Calculate absolute, real, and image part of complex wave.

    Args:
        type('absolute' or 'real' or 'imag'): operation type.
    """

    def __init__(self, type):
        self._type = type

    def _execute(self, wave, **kwargs):
        if self._type == "absolute":
            data = da.absolute(wave.data)
        if self._type == "real":
            data = da.real(wave.data)
        if self._type == "imag":
            data = da.imag(wave.data)
        return DaskWave(data, *wave.axes, **wave.note)

    def getParameters(self):
        return {"type": self._type}


class PhaseFilter(FilterInterface):
    """
    Rotate complex value by *rot*

    Args:  
        rot(float): rotation angle.
        unit('deg' or 'rad'): unit used to specify rotation angle.
    """

    def __init__(self, rot, unit="deg"):
        if unit == "rad":
            self._rot = rot / np.pi * 180
        else:
            self._rot = rot

    def _execute(self, wave, **kwargs):
        data = wave.data * np.exp(1j * self._rot / 180 * np.pi)
        return DaskWave(data, *wave.axes, **wave.note)

    def getParameters(self):
        return {"rot": self._rot}


class NanToNumFilter(FilterInterface):
    """
    Replace np.nan to *value*.

    Args:
        value(any): value by which replace np.nan.
    """

    def __init__(self, value):
        self._value = value

    def _execute(self, wave, **kwargs):
        data = da.nan_to_num(wave.data, self._value)
        return DaskWave(data, *wave.axes, **wave.note)

    def getParameters(self):
        return {"value": self._value}
