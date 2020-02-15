from ..filter.Segmentation import *
from .FilterGroupSetting import *
from ..filtersGUI import filterGroups

from ...BasicWidgets.Commons.ScientificSpinBox import ScientificSpinBox

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
        self._layout = QGridLayout()
        self._method = QComboBox()
        self._method.addItem('Median')
        self._method.addItem('Gaussian')
        self._bsize = QSpinBox()
        self._bsize.setRange(1, 100000)
        self._bsize.setValue(11)
        self._c = QSpinBox()
        self._c.setRange(-1000000, 100000)
        self._c.setValue(2)
        self._layout.addWidget(QLabel('Method'), 0, 0)
        self._layout.addWidget(self._method, 1, 0)
        self._layout.addWidget(QLabel('Block size'), 0, 1)
        self._layout.addWidget(self._bsize, 1, 1)
        self._layout.addWidget(QLabel('C'), 0, 2)
        self._layout.addWidget(self._c, 1, 2)
        self.setLayout(self._layout)

    def GetFilter(self):
        return AdaptiveThresholdFilter(self._bsize.value(), self._c.value(), self._method.currentText())

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
