from ..filter.Frequency import *
from ..filtersGUI import *
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


class LowPassSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
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

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, LowPassFilter):
            return True

    def GetFilter(self):
        return LowPassFilter(self._order.value(), self._cut.value(), self._axes.GetChecked())

    def parseFromFilter(self, f):
        obj = LowPassSetting(None, self.dim, self.loader)
        order, cutoff, axes = f.getParams()
        obj._cut.setValue(cutoff)
        obj._order.setValue(order)
        obj._axes.SetChecked(axes)
        return obj


class HighPassSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self._layout = QHBoxLayout()
        self._cut = QDoubleSpinBox()
        self._cut.setDecimals(3)
        self._cut.setRange(0, 1)
        self._cut.setValue(0.8)
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

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, HighPassFilter):
            return True

    def GetFilter(self):
        return HighPassFilter(self._order.value(), self._cut.value(), self._axes.GetChecked())

    def parseFromFilter(self, f):
        obj = HighPassSetting(None, self.dim, self.loader)
        order, cutoff, axes = f.getParams()
        obj._cut.setValue(cutoff)
        obj._order.setValue(order)
        obj._axes.SetChecked(axes)
        return obj


class BandPassSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
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

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, BandPassFilter):
            return True

    def GetFilter(self):
        return BandPassFilter(self._order.value(), [self._cut1.value(), self._cut2.value()], self._axes.GetChecked())

    def parseFromFilter(self, f):
        obj = BandPassSetting(None, self.dim, self.loader)
        order, cutoff, axes = f.getParams()
        obj._cut1.setValue(cutoff[0])
        obj._cut2.setValue(cutoff[1])
        obj._order.setValue(order)
        obj._axes.SetChecked(axes)
        return obj


class BandStopSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
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

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, BandStopFilter):
            return True

    def GetFilter(self):
        return BandStopFilter(self._order.value(), [self._cut1.value(), self._cut2.value()], self._axes.GetChecked())

    def parseFromFilter(self, f):
        obj = BandStopSetting(None, self.dim, self.loader)
        order, cutoff, axes = f.getParams()
        obj._cut1.setValue(cutoff[0])
        obj._cut2.setValue(cutoff[1])
        obj._order.setValue(order)
        obj._axes.SetChecked(axes)
        return obj


class FourierSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self.dim = dim
        self._layout = QHBoxLayout()
        self._combo = QComboBox()
        self._combo.addItem('forward', 'forward')
        self._combo.addItem('backward', 'backward')
        self._process = QComboBox()
        self._process.addItem('absolute', 'absolute')
        self._process.addItem('real', 'real')
        self._process.addItem('imag', 'imag')
        self._process.addItem('phase', 'phase')
        self._axes = AxisCheckLayout(dim)
        self._layout.addWidget(QLabel('Direction'))
        self._layout.addWidget(self._combo)
        self._layout.addWidget(QLabel('Process'))
        self._layout.addWidget(self._process)
        self._layout.addLayout(self._axes)
        self.setLayout(self._layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, FourierFilter):
            return True

    def GetFilter(self):
        return FourierFilter(self._axes.GetChecked(), type=self._combo.currentText(), process=self._process.currentText())

    def parseFromFilter(self, f):
        obj = FourierSetting(None, self.dim, self.loader)
        axes, type, process = f.getParams()
        obj._axes.SetChecked(axes)
        obj._process.setCurrentIndex(obj._process.findData(process))
        obj._combo.setCurrentIndex(obj._combo.findData(type))
        return obj


filterGroups['Frequency Filter'] = FrequencySetting
filterGroups['Fourier Filter'] = FourierSetting
