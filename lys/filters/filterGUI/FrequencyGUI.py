from lys import filters
from ..filtersGUI import filterGroups, FilterGroupSetting, FilterSettingBase, filterGUI
from .CommonWidgets import *


class FrequencySetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Lowpass': LowPassSetting,
            'Highpass': HighPassSetting,
            'Bandpass': BandPassSetting,
            'Bandstop': BandStopSetting
        }
        return d


class _Setting1(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self._layout = QHBoxLayout()
        self._cut = QDoubleSpinBox()
        self._cut.setDecimals(3)
        self._cut.setRange(0, 1)
        self._cut.setValue(0.2)
        self._order = QSpinBox()
        self._order.setRange(0, 1000)
        self._order.setValue(1)
        self._layout.addWidget(QLabel('Order'))
        self._layout.addWidget(self._order)
        self._layout.addWidget(QLabel('Cutoff'))
        self._layout.addWidget(self._cut)

        self._axes = AxisCheckLayout(dim)
        vbox = QVBoxLayout()
        vbox.addLayout(self._layout)
        vbox.addLayout(self._axes)
        self.setLayout(vbox)

    def getParameters(self):
        return {"order": self._order.value(), "cutoff": self._cut.value(), "axes": self._axes.GetChecked()}

    def setParameters(self, order, cutoff, axes):
        self._cut.setValue(cutoff)
        self._order.setValue(order)
        self._axes.SetChecked(axes)


@filterGUI(filters.LowPassFilter)
class LowPassSetting(_Setting1):
    pass


@filterGUI(filters.HighPassFilter)
class HighPassSetting(_Setting1):
    pass


class _Setting2(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self._layout = QHBoxLayout()
        self._cut1 = QDoubleSpinBox()
        self._cut1.setDecimals(3)
        self._cut1.setRange(0, 1)
        self._cut1.setValue(0.2)
        self._cut2 = QDoubleSpinBox()
        self._cut2.setDecimals(3)
        self._cut2.setRange(0, 1)
        self._cut2.setValue(0.8)
        self._order = QSpinBox()
        self._order.setRange(0, 1000)
        self._order.setValue(1)
        self._layout.addWidget(QLabel('Order'))
        self._layout.addWidget(self._order)
        self._layout.addWidget(QLabel('Low'))
        self._layout.addWidget(self._cut1)
        self._layout.addWidget(QLabel('High'))
        self._layout.addWidget(self._cut2)
        self._axes = AxisCheckLayout(dim)
        vbox = QVBoxLayout()
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


@filterGUI(filters.BandPassFilter)
class BandPassSetting(_Setting2):
    pass


@filterGUI(filters.BandStopFilter)
class BandStopSetting(_Setting2):
    pass


@filterGUI(filters.FourierFilter)
class FourierSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self.dim = dim
        self._combo = QComboBox()
        self._combo.addItem('forward', 'forward')
        self._combo.addItem('backward', 'backward')
        self._process = QComboBox()
        self._process.addItem('absolute', 'absolute')
        self._process.addItem('real', 'real')
        self._process.addItem('imag', 'imag')
        self._process.addItem('phase', 'phase')
        self._process.addItem('complex', 'complex')
        self._axes = AxisCheckLayout(dim)
        self._window = QComboBox()
        self._window.addItem("Rect", "Rect")
        self._window.addItem("Hann", "Hann")
        self._window.addItem("Hamming", "Hamming")
        self._window.addItem("Blackman", "Blackman")

        self._layout = QGridLayout()
        self._layout.addWidget(QLabel('Direction'), 0, 0)
        self._layout.addWidget(QLabel('Process'), 0, 1)
        self._layout.addWidget(QLabel('Window'), 0, 2)
        self._layout.addWidget(QLabel('Axes'), 0, 3)
        self._layout.addWidget(self._combo, 1, 0)
        self._layout.addWidget(self._process, 1, 1)
        self._layout.addWidget(self._window, 1, 2)
        self._layout.addLayout(self._axes, 1, 3)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"axes": self._axes.GetChecked(), "type": self._combo.currentText(), "process": self._process.currentText(), "window": self._window.currentText(), "roll": True}

    def setParameters(self, axes, type, process, window, roll):
        self._axes.SetChecked(axes)
        self._process.setCurrentIndex(self._process.findData(process))
        self._combo.setCurrentIndex(self._combo.findData(type))
        self._window.setCurrentIndex(self._window.findData(window))


filterGroups['Frequency Filter'] = FrequencySetting
filterGroups['Fourier Filter'] = FourierSetting
