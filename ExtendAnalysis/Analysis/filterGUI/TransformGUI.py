from ..filter.Transform import *
from ..filtersGUI import *
from ExtendAnalysis import ScientificSpinBox


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


class SetAxisSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
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

    def GetFilter(self):
        if self._type.currentIndex() == 0:
            type = "stop"
        else:
            type = "step"
        return SetAxisFilter(self._axis.currentIndex(), self._val1.value(), self._val2.value(), type)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SetAxisFilter):
            return True

    def parseFromFilter(self, f):
        obj = SetAxisSetting(None, self.dim, self.loader)
        axis, val1, val2, type = f.getParams()
        obj._axis.setCurrentIndex(axis)
        if type == "stop":
            obj._type.setCurrentIndex(0)
        else:
            obj._type.setCurrentIndex(1)
        obj._val1.setValue(val1)
        obj._val2.setValue(val2)
        return obj


class ShiftSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._layout = QGridLayout()
        self._dim = dimension
        self._values = []
        for i in range(dimension):
            wid = ScientificSpinBox()
            self._values.append(wid)
            self._layout.addWidget(QLabel('Axis' + str(i + 1)), 0, i)
            self._layout.addWidget(wid, 1, i)
        self.setLayout(self._layout)

    def GetFilter(self):
        return AxisShiftFilter([v.value() for v in self._values], list(range(self._dim)))

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, AxisShiftFilter):
            return True

    def parseFromFilter(self, f):
        obj = ShiftSetting(None, self.dim, self.loader)
        shift, axes = f.getParams()
        for s, ax in zip(shift, axes):
            obj._values[ax].setValue(s)
        return obj


class ImageShiftSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
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

    def GetFilter(self):
        return ShiftFilter([v.value() for v in self._values])

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, ShiftFilter):
            return True

    def parseFromFilter(self, f):
        obj = ImageShiftSetting(None, self.dim, self.loader)
        shift = f.getParams()
        for ax, s in enumerate(shift):
            obj._values[ax].setValue(s)
        return obj


class MagnificationSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
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

    def GetFilter(self):
        return MagnificationFilter([v.value() for v in self._values], list(range(self._dim)))

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, MagnificationFilter):
            return True

    def parseFromFilter(self, f):
        obj = MagnificationSetting(None, self.dim, self.loader)
        shift, axes = f.getParams()
        for s, ax in zip(shift, axes):
            obj._values[ax].setValue(s)
        return obj


class Rotation2DSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._layout = QHBoxLayout()
        self._rot = ScientificSpinBox()
        self._layout.addWidget(QLabel('Rotation'))
        self._layout.addWidget(self._rot)
        self.setLayout(self._layout)

    def GetFilter(self):
        return Rotation2DFilter(self._rot.value())

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, Rotation2DFilter):
            return True

    def parseFromFilter(self, f):
        obj = Rotation2DSetting(None, self.dim, self.loader)
        r = f.getParams()
        obj._rot.setValue(r)
        return obj


filterGroups["Transform"] = TransformSetting
