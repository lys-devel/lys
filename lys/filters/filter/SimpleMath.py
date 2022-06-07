import numpy as np
import dask.array as da

from lys import DaskWave
from lys.Qt import QtWidgets
from lys.filters import FilterSettingBase, filterGUI, addFilter

from .FilterInterface import FilterInterface
from .CommonWidgets import ScientificSpinBox


class SimpleMathFilter(FilterInterface):
    """
    Apply simple mathematical calculation.

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


@filterGUI(SimpleMathFilter)
class _SimpleMathSetting(FilterSettingBase):
    _ops = ["+", "-", "*", "/", "**"]

    def __init__(self, dim):
        super().__init__(dim)
        self._val = QtWidgets.QLineEdit()
        self._val.setText("0")
        self._type = QtWidgets.QComboBox()
        self._type.addItems(self._ops)

        self._layout = QtWidgets.QHBoxLayout()
        self._layout.addWidget(QtWidgets.QLabel('data'))
        self._layout.addWidget(self._type)
        self._layout.addWidget(self._val)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"type": self._type.currentText(), "value": eval(self._val.text())}

    def setParameters(self, type, value):
        self._val.setText(str(value))
        self._type.setCurrentIndex(self._ops.index(type))


@filterGUI(ComplexFilter)
class _ComplexSetting(FilterSettingBase):
    types = ["absolute", "real", "imag"]

    def __init__(self, dimension=2):
        super().__init__(dimension)
        layout = QtWidgets.QHBoxLayout()
        self._combo = QtWidgets.QComboBox()
        self._combo.addItems(self.types)
        layout.addWidget(self._combo)
        self.setLayout(layout)

    def getParameters(self):
        return {"type": self._combo.currentText()}

    def setParameters(self, type):
        self._combo.setCurrentIndex(self.types.index(type))


@filterGUI(PhaseFilter)
class _PhaseSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        layout = QtWidgets.QHBoxLayout()
        self._phase = ScientificSpinBox()
        layout.addWidget(self._phase)
        layout.addWidget(QtWidgets.QLabel("deg"))
        self.setLayout(layout)

    def getParameters(self):
        return {"rot": self._phase.value(), "unit": "deg"}

    def setParameters(self, rot):
        self._phase.setValue(rot)


@filterGUI(NanToNumFilter)
class _NanToNumSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._val = QtWidgets.QLineEdit()
        self._val.setText("0")
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Value: "))
        layout.addWidget(self._val)
        self.setLayout(layout)

    def getParameters(self):
        return {"value": eval(self._val.text())}

    def setParameters(self, value):
        self._val.setText(str(value))


addFilter(SimpleMathFilter, gui=_SimpleMathSetting, guiName="Simple Math", guiGroup="Simple Math")
addFilter(ComplexFilter, gui=_ComplexSetting, guiName="Complex", guiGroup="Simple Math")
addFilter(PhaseFilter, gui=_PhaseSetting, guiName="Rotate phase", guiGroup="Simple Math")
addFilter(NanToNumFilter, gui=_NanToNumSetting, guiName="Replace NaN", guiGroup="Simple Math")
