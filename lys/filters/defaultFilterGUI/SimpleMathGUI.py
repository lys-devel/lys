from lys import filters
from ..filtersGUI import filterGroups, FilterGroupSetting, FilterSettingBase, filterGUI
from .CommonWidgets import *


class SimpleMathCalcSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Simple': SimpleMathSetting,
            'Complex': ComplexSetting,
            'Phase': PhaseSetting,
            'Replace nan': NanToNumSetting,
        }
        return d


@filterGUI(filters.SimpleMathFilter)
class SimpleMathSetting(FilterSettingBase):
    _ops = ["+", "-", "*", "/", "**"]

    def __init__(self, dim):
        super().__init__(dim)
        self._val = QLineEdit()
        self._val.setText("0")
        self._type = QComboBox()
        self._type.addItems(self._ops)

        self._layout = QHBoxLayout()
        self._layout.addWidget(QLabel('data'))
        self._layout.addWidget(self._type)
        self._layout.addWidget(self._val)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"type": self._type.currentText(), "value": eval(self._val.text())}

    def setParameters(self, type, value):
        self._val.setText(str(value))
        self._type.setCurrentIndex(self._ops.index(type))


@filterGUI(filters.ComplexFilter)
class ComplexSetting(FilterSettingBase):
    types = ["absolute", "real", "imag"]

    def __init__(self, dimension=2):
        super().__init__(dimension)
        layout = QHBoxLayout()
        self._combo = QComboBox()
        self._combo.addItems(self.types)
        layout.addWidget(self._combo)
        self.setLayout(layout)

    def getParameters(self):
        return {"type": self._combo.currentText()}

    def setParameters(self, type):
        self._combo.setCurrentIndex(self.types.index(type))


@filterGUI(filters.PhaseFilter)
class PhaseSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        layout = QHBoxLayout()
        self._phase = ScientificSpinBox()
        layout.addWidget(self._phase)
        layout.addWidget(QLabel("deg"))
        self.setLayout(layout)

    def getParameters(self):
        return {"rot": self._phase.value(), "unit": "deg"}

    def setParameters(self, rot):
        self._phase.setValue(rot)


@filterGUI(filters.NanToNumFilter)
class NanToNumSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._val = QLineEdit()
        self._val.setText("0")
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Value: "))
        layout.addWidget(self._val)
        self.setLayout(layout)

    def getParameters(self):
        return {"value": eval(self._val.text())}

    def setParameters(self, value):
        self._val.setText(str(value))


filterGroups['Simple Math'] = SimpleMathCalcSetting
