from PyQt5.QtWidgets import QVBoxLayout
from lys import filters
from ..filtersGUI import filterGroups, FilterGroupSetting, FilterSettingBase, filterGUI
from .CommonWidgets import *


class SegmentSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Threshold': ThresholdSetting,
            '*Adaptive Threshold': AdaptiveThresholdSetting,
        }
        return d


@filterGUI(filters.AdaptiveThresholdFilter)
class AdaptiveThresholdSetting(FilterSettingBase):
    finished = pyqtSignal()

    def __init__(self, dimension=2):
        super().__init__(dimension)
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

    def getParameters(self):
        return {"size": self._bsize.value(), "c": self._c.value(), "mode": self._method.currentText(), "output": self._output.currentText(), "axes": [c.getAxis() for c in self.axes]}

    def setParameters(self, size, c, mode, output, axes):
        self._bsize.setValue(size)
        self._c.setValue(c)
        self._method.setCurrentText(mode)
        self._output.setCurrentText(output)
        for c, i in zip(self.axes, axes):
            c.setAxis(i)


@filterGUI(filters.ThresholdFilter)
class ThresholdSetting(FilterSettingBase):
    finished = pyqtSignal()

    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = QHBoxLayout()
        self._c = ScientificSpinBox()
        self._c.setValue(1)
        self._layout.addWidget(QLabel('Threshold'))
        self._layout.addWidget(self._c)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"threshold": self._c.value(), "output": "Mask"}

    def setParameters(self, threshold, output):
        self._c.setValue(threshold)


filterGroups['Segmentation'] = SegmentSetting
