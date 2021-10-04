from lys import filters
from ..filtersGUI import filterGroups, FilterGroupSetting, FilterSettingBase, filterGUI
from .CommonWidgets import *


class TransformSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Set axis': SetAxisSetting,
            'Shift': ShiftSetting,
            'ImageShift': ImageShiftSetting,
            'Magnify': MagnificationSetting,
            'Rotation2D': Rotation2DSetting,
        }
        return d


@filterGUI(filters.SetAxisFilter)
class SetAxisSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = QGridLayout()
        self._axis = QComboBox()
        for i in range(dimension):
            self._axis.addItem("Axis" + str(i + 1))
        self._type = QComboBox()
        self._type.addItem("Start & Stop")
        self._type.addItem("Start & Step")
        self._val1 = ScientificSpinBox()
        self._val2 = ScientificSpinBox()
        self._val2.setValue(1)
        self._layout.addWidget(QLabel('Axis'), 0, 0)
        self._layout.addWidget(QLabel('Type'), 0, 1)
        self._layout.addWidget(QLabel('Start'), 0, 2)
        self._layout.addWidget(QLabel('Stop/Step'), 0, 3)
        self._layout.addWidget(self._axis, 1, 0)
        self._layout.addWidget(self._type, 1, 1)
        self._layout.addWidget(self._val1, 1, 2)
        self._layout.addWidget(self._val2, 1, 3)
        self.setLayout(self._layout)

    def getParameters(self):
        if self._type.currentIndex() == 0:
            type = "stop"
        else:
            type = "step"
        return {"axis": self._axis.currentIndex(), "val1": self._val1.value(), "val2": self._val2.value(), "type": type}

    def setParameters(self, axis, val1, val2, type):
        self._axis.setCurrentIndex(axis)
        if type == "stop":
            self._type.setCurrentIndex(0)
        else:
            self._type.setCurrentIndex(1)
        self._val1.setValue(val1)
        self._val2.setValue(val2)


@filterGUI(filters.AxisShiftFilter)
class ShiftSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = QGridLayout()
        self._dim = dimension
        self._values = []
        for i in range(dimension):
            wid = ScientificSpinBox()
            self._values.append(wid)
            self._layout.addWidget(QLabel('Axis' + str(i + 1)), 0, i)
            self._layout.addWidget(wid, 1, i)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"shift": [v.value() for v in self._values], "axes": list(range(self._dim))}

    def setParameters(self, shift, axes):
        for s, ax in zip(shift, axes):
            self._values[ax].setValue(s)


@filterGUI(filters.ShiftFilter)
class ImageShiftSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = QGridLayout()
        self._dim = dimension
        self._values = []
        for i in range(dimension):
            wid = QSpinBox()
            wid.setRange(-1000000, 1000000)
            self._values.append(wid)
            self._layout.addWidget(QLabel('Axis' + str(i + 1)), 0, i)
            self._layout.addWidget(wid, 1, i)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"shift": [v.value() for v in self._values]}

    def setParameters(self, shift):
        for ax, s in enumerate(shift):
            self._values[ax].setValue(s)


@filterGUI(filters.MagnificationFilter)
class MagnificationSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._layout = QGridLayout()
        self._dim = dimension
        self._values = []
        for i in range(dimension):
            wid = ScientificSpinBox()
            wid.setValue(1)
            self._values.append(wid)
            self._layout.addWidget(QLabel('Axis' + str(i + 1)), 0, i)
            self._layout.addWidget(wid, 1, i)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"mag": [v.value() for v in self._values], "axes": list(range(self._dim))}

    def setParameters(self, mag, axes):
        for s, ax in zip(mag, axes):
            self._values[ax].setValue(s)


@filterGUI(filters.Rotation2DFilter)
class Rotation2DSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._rot = ScientificSpinBox()
        self._layout = QHBoxLayout()
        self._layout.addWidget(QLabel('Rotation'))
        self._layout.addWidget(self._rot)

        self.axis1 = AxisSelectionLayout("Axis 1", self.dim, 0)
        self.axis2 = AxisSelectionLayout("Axis 2", self.dim, 1)

        lay = QVBoxLayout()
        lay.addLayout(self._layout)
        lay.addLayout(self.axis1)
        lay.addLayout(self.axis2)
        self.setLayout(lay)

    def getParameters(self):
        return {"angle": self._rot.value(), "axes": (self.axis1.getAxis(), self.axis2.getAxis())}

    def setParameters(self, angle, axes):
        self._rot.setValue(angle)
        self.axis1.setAxis(axes[0])
        self.axis2.setAxis(axes[1])


filterGroups["Transform"] = TransformSetting
