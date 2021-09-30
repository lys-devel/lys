from PyQt5.QtWidgets import QVBoxLayout
from ..filter.Segmentation import *
from ..filtersGUI import *
from lys import ScientificSpinBox
from .CommonWidgets import *


class SegmentSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Threshold': ThresholdSetting,
            '*Adaptive Threshold': AdaptiveThresholdSetting,
        }
        return d


class AdaptiveThresholdSetting(FilterSettingBase):
    finished = pyqtSignal()

    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._method = QComboBox()
        self._method.addItem('Median')
        self._method.addItem('Gaussian')
        self._output = QComboBox()
        self._output.addItems(['Mask', 'Mask (inv)', 'Masked data', 'Masked data (inv)'])
        self._bsize = QSpinBox()
        self._bsize.setRange(1, 100000)
        self._bsize.setValue(11)
        self._c = ScientificSpinBox()
        self._c.setValue(2)

        self._layout = QGridLayout()
        self._layout.addWidget(QLabel('Method'), 0, 0)
        self._layout.addWidget(self._method, 1, 0)
        self._layout.addWidget(QLabel('Output'), 0, 1)
        self._layout.addWidget(self._output, 1, 1)
        self._layout.addWidget(QLabel('Block size'), 0, 2)
        self._layout.addWidget(self._bsize, 1, 2)
        self._layout.addWidget(QLabel('C'), 0, 3)
        self._layout.addWidget(self._c, 1, 3)

        self.axes = [AxisSelectionLayout("Axis1", dim=dimension, init=0), AxisSelectionLayout("Axis2", dim=dimension, init=1)]
        lv = QVBoxLayout()
        lv.addLayout(self._layout)
        lv.addLayout(self.axes[0])
        lv.addLayout(self.axes[1])
        self.setLayout(lv)

    def GetFilter(self):
        axes = [c.getAxis() for c in self.axes]
        return AdaptiveThresholdFilter(self._bsize.value(), self._c.value(), self._method.currentText(), self._output.currentText(), axes)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, AdaptiveThresholdFilter):
            return True

    def parseFromFilter(self, f):
        params = f.getParams()
        obj = AdaptiveThresholdSetting(None, self.dim, self.loader)
        obj._bsize.setValue(params[0])
        obj._c.setValue(params[1])
        obj._method.setCurrentText(params[2])
        obj._output.setCurrentText(params[3])
        for c, i in zip(obj.axes, params[4]):
            c.setAxis(i)
        return obj


class ThresholdSetting(FilterSettingBase):
    finished = pyqtSignal()

    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._layout = QHBoxLayout()
        self._c = ScientificSpinBox()
        self._c.setValue(1)
        self._layout.addWidget(QLabel('Threshold'))
        self._layout.addWidget(self._c)
        self.setLayout(self._layout)

    def GetFilter(self):
        return ThresholdFilter(self._c.value())

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, ThresholdFilter):
            return True

    def parseFromFilter(self, f):
        param = f.getParams()
        obj = ThresholdSetting(None, self.dim, self.loader)
        obj._c.setValue(param)
        return obj


filterGroups['Segmentation'] = SegmentSetting
