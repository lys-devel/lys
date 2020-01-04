from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from ExtendAnalysis import *
from .filters import *
import _pickle as cPickle


class PreFilterSetting(QWidget):
    filterAdded = pyqtSignal(QWidget)
    filterDeleted = pyqtSignal(QWidget)

    def __init__(self, parent, dimension=2, loader=None):
        super().__init__()
        h1 = QHBoxLayout()
        self.root = RootSetting(self, dimension, loader, h1)
        self.root.filterChanged.connect(self._filt)
        self._layout = QVBoxLayout()
        self._layout.addLayout(h1)
        self.setLayout(self._layout)
        self._child = None

    def _filt(self, widget):
        if self._child is not None:
            self._layout.removeWidget(self._child)
            self._child.deleteLater()
            self._child = None
        if isinstance(widget, DeleteSetting):
            self.filterDeleted.emit(self)
        else:
            self._layout.addWidget(widget)
            self._child = widget
            self.filterAdded.emit(self)

    def GetFilter(self):
        if self._child is not None:
            return self._child.GetFilter()

    def SetFilter(self, filt):
        obj = self.root.parseFromFilter(filt)
        self._filt(obj)

    def clear(self, dimension=2):
        self.root._combo.setCurrentIndex(0)
        self.root.setDimension(dimension)


class FilterGroupSetting(QWidget):
    filterChanged = pyqtSignal(QWidget)

    def __init__(self, parent, dimension=2, loader=None, layout=None):
        super().__init__()
        self.dim = dimension
        self.loader = loader
        self._filters = self._filterList()

        self._layout = layout
        self._combo = QComboBox()
        for f in self._filters.keys():
            self._combo.addItem(f, f)
        self._combo.currentTextChanged.connect(self._update)
        vlayout = QVBoxLayout()
        vlayout.addWidget(QLabel('Type'))
        vlayout.addWidget(self._combo)
        self.setLayout(vlayout)
        self._layout.addWidget(self)
        self._childGroup = None
        self._update(self._combo.currentText())

    @classmethod
    def _filterList(cls):
        return filterGroups

    def _update(self, text=None):
        if text is None:
            text = self._combo.currentText()
        if text in self._filters:
            self._removeChildGroup()
            if issubclass(self._filters[text], FilterGroupSetting):
                self.filter = self._filters[text](None, self.dim, loader=self.loader, layout=self._layout)
                self._addGroup(self.filter)
            else:
                self.filter = self._filters[text](None, self.dim, loader=self.loader)
                self.filterChanged.emit(self.filter)

    def _addGroup(self, g):
        self._childGroup = g
        g.filterChanged.connect(self.filterChanged)
        self._layout.addWidget(g)
        g._update()

    def _removeChildGroup(self):
        if self._childGroup is not None:
            self._childGroup._removeChildGroup()
            self._childGroup.filterChanged.disconnect(self.filterChanged)
            self._layout.removeWidget(self._childGroup)
            self._childGroup.deleteLater()
            self._childGroup = None

    @classmethod
    def _havingFilter(cls, f):
        for key, s in cls._filterList().items():
            if s._havingFilter(f) is not None:
                return key

    def parseFromFilter(self, f):
        name = self._havingFilter(f)
        if name is not None:
            self._combo.setCurrentIndex(self._combo.findData(name))
        return self.filter.parseFromFilter(f)

    def setDimension(self, dimension):
        self.dim = dimension


class RootSetting(FilterGroupSetting):
    filterAdded = pyqtSignal(QWidget)
    filterDeleted = pyqtSignal(QWidget)
    @classmethod
    def _filterList(cls):
        return filterGroups


class DeleteSetting(QWidget):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(None)

    @classmethod
    def _havingFilter(cls, f):
        return None


class SmoothingSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Median': MedianSetting,
            'Average': AverageSetting,
            'Gaussian': GaussianSetting
            # 'Bilateral': BilateralSetting
        }
        return d

class SpinBoxOverOne(QSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimum(1)
        self.setValue(1)

class OddSpinBox(QSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimum(1)
        self.setSingleStep(2)
        self.setValue(3)
        self.valueChanged.connect(self.valChanged)

    def valChanged(self, val):
        if val % 2 == 0:
            self.setValue(val - 1)


class _kernelSizeLayout(QGridLayout):
    def __init__(self, dimension=2, odd = True):
        super().__init__()
        self.addWidget(QLabel('Kernel Size'), 1, 0)
        if odd:
            spin=OddSpinBox
        else:
            spin=SpinBoxOverOne
        self._kernels = [spin() for d in range(dimension)]
        for i, k in enumerate(self._kernels):
            self.addWidget(QLabel('Axis' + str(i + 1)), 0, i + 1)
            self.addWidget(k, 1, i + 1)

    def getKernelSize(self):
        return [k.value() for k in self._kernels]

    def setKernelSize(self, val):
        for k, v in zip(self._kernels, val):
            k.setValue(v)


class _kernelSigmaLayout(QGridLayout):
    def __init__(self, dimension=2):
        super().__init__()
        self.addWidget(QLabel('Sigma'), 1, 0)
        self._kernels = [QDoubleSpinBox() for d in range(dimension)]
        for i, k in enumerate(self._kernels):
            k.setMinimum(0)
            self.addWidget(QLabel('Axis' + str(i + 1)), 0, i + 1)
            self.addWidget(k, 1, i + 1)

    def getKernelSigma(self):
        return [k.value() for k in self._kernels]

    def setKernelSigma(self, val):
        for k, v in zip(self._kernels, val):
            k.setValue(v)


class FilterSettingBase(QWidget):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(None)
        self.dim = dimension
        self.loader = loader


class MedianSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._layout = _kernelSizeLayout(dimension)
        self.setLayout(self._layout)

    def GetFilter(self):
        return MedianFilter(self._layout.getKernelSize())

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, MedianFilter):
            return True

    def parseFromFilter(self, f):
        obj = MedianSetting(None, self.dim, self.loader)
        obj._layout.setKernelSize(f.getKernel())
        return obj


class AverageSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._layout = _kernelSizeLayout(dimension)
        self.setLayout(self._layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, AverageFilter):
            return True

    def GetFilter(self):
        return AverageFilter(self._layout.getKernelSize())

    def parseFromFilter(self, f):
        obj = AverageSetting(None, self.dim, self.loader)
        obj._layout.setKernelSize(f.getKernel())
        return obj


class GaussianSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._layout = _kernelSigmaLayout(dimension)
        self.setLayout(self._layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, GaussianFilter):
            return True

    def GetFilter(self):
        return GaussianFilter(self._layout.getKernelSigma())

    def parseFromFilter(self, f):
        obj = GaussianSetting(None, self.dim, self.loader)
        obj._layout.setKernelSigma(f.getKernel())
        return obj


class BilateralSetting(QWidget):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent)
        self._layout = QHBoxLayout()
        self._kernel = QSpinBox()
        self._kernel.setMinimum(3)
        self._kernel.setValue(5)
        self._s_color = QSpinBox()
        self._s_color.setMinimum(1)
        self._s_color.setValue(7)
        self._s_space = QSpinBox()
        self._s_space.setMinimum(1)
        self._s_space.setValue(7)
        self._layout.addWidget(QLabel('Kernel Size'))
        self._layout.addWidget(self._kernel)
        self._layout.addWidget(QLabel('Sigma color'))
        self._layout.addWidget(self._s_color)
        self._layout.addWidget(QLabel('Sigma space'))
        self._layout.addWidget(self._s_space)
        self.setLayout(self._layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, BilateralFilter):
            return True

    def GetFilter(self):
        return BilateralFilter(self._kernel.value(), self._s_color.value(), self._s_space.value())


class AxisCheckLayout(QHBoxLayout):
    def __init__(self, dim):
        super().__init__()
        self._axes = [QCheckBox("Axis" + str(i)) for i in range(dim)]
        for a in self._axes:
            self.addWidget(a)

    def GetChecked(self):
        axes = []
        for i, a in enumerate(self._axes):
            if a.isChecked():
                axes.append(i)
        return axes

    def SetChecked(self, axes):
        for i, a in enumerate(self._axes):
            if i in axes:
                a.setChecked(True)
            else:
                a.setChecked(False)


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


class DifferentialSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Prewitt': PrewittSetting,
            'Sobel': SobelSetting,
            'Laplacian': LaplacianSetting,
            'Sharpen': SharpenSetting
        }
        return d


class PrewittSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self._layout = AxisCheckLayout(dim)
        self.setLayout(self._layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, PrewittFilter):
            return True

    def GetFilter(self):
        return PrewittFilter(self._layout.GetChecked())

    def parseFromFilter(self, f):
        obj = PrewittSetting(None, self.dim, self.loader)
        axes = f.getAxes()
        obj._layout.SetChecked(axes)
        return obj


class SobelSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self._layout = AxisCheckLayout(dim)
        self.setLayout(self._layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SobelFilter):
            return True

    def GetFilter(self):
        return SobelFilter(self._layout.GetChecked())

    def parseFromFilter(self, f):
        obj = SobelSetting(None, self.dim, self.loader)
        axes = f.getAxes()
        obj._layout.SetChecked(axes)
        return obj


class LaplacianSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self._layout = AxisCheckLayout(dim)
        self.setLayout(self._layout)

    @classmethod
    def _havingFilter(cls, f):
        if type(f) == LaplacianFilter:
            return True

    def GetFilter(self):
        return LaplacianFilter(self._layout.GetChecked())

    def parseFromFilter(self, f):
        obj = LaplacianSetting(None, self.dim, self.loader)
        axes = f.getAxes()
        obj._layout.SetChecked(axes)
        return obj


class SharpenSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self._layout = AxisCheckLayout(dim)
        self.setLayout(self._layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SharpenFilter):
            return True

    def GetFilter(self):
        return SharpenFilter(self._layout.GetChecked())

    def parseFromFilter(self, f):
        obj = SharpenSetting(None, self.dim, self.loader)
        axes = f.getAxes()
        obj._layout.SetChecked(axes)
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


class SymmetricOperationSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Reverse': ReverseSetting,
            'Roll': RollSetting,
        }
        return d


class ReverseSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self._axes = AxisCheckLayout(dim)
        self.setLayout(self._axes)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, ReverseFilter):
            return True

    def GetFilter(self):
        return ReverseFilter(self._axes.GetChecked())

    def parseFromFilter(self, f):
        obj = ReverseSetting(None, self.dim, self.loader)
        obj._axes.SetChecked(f.getAxes())
        return obj


class RollSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        layout = QHBoxLayout()
        self._combo = QComboBox()
        self._combo.addItem("1/2")
        self._combo.addItem("1/4")
        self._combo.addItem("-1/4")
        self._axes = AxisCheckLayout(dim)
        layout.addWidget(self._combo)
        layout.addLayout(self._axes)
        self.setLayout(layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, RollFilter):
            return True

    def GetFilter(self):
        return RollFilter(self._combo.currentText(), self._axes.GetChecked())

    def parseFromFilter(self, f):
        obj = RollSetting(None, self.dim, self.loader)
        type, axes = f.getParams()
        obj._axes.SetChecked(axes)
        obj._combo.setCurrentText(type)
        return obj


class SimpleMathSetting(FilterGroupSetting):
    @classmethod
    def _filterList(cls):
        d = {
            'Add': AddSetting,
            'Subtract': SubtractSetting,
            'Multiply': MultSetting,
            'Devide': DevideSetting,
            'Pow': PowSetting,
        }
        return d


class SimpleMathSettingBase(FilterSettingBase):
    def __init__(self, parent, dim, loader=None, type=""):
        super().__init__(parent, dim, loader)
        self._layout = QHBoxLayout()
        self._val = QDoubleSpinBox()
        self._val.setDecimals(5)
        self._layout.addWidget(QLabel('Value'))
        self._layout.addWidget(self._val)
        self._type = type
        self.setLayout(self._layout)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SimpleMathFilter):
            if f._type == self._type:
                return True

    def GetFilter(self):
        return SimpleMathFilter(self._type, self._val.value())


class AddSetting(SimpleMathSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader, "+")

    def parseFromFilter(self, f):
        obj = AddSetting(None, self.dim, self.loader)
        obj._val.setValue(f._val)
        return obj


class SubtractSetting(SimpleMathSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader, "-")

    def parseFromFilter(self, f):
        obj = SubtractSetting(None, self.dim, self.loader)
        obj._val.setValue(f._val)
        return obj


class MultSetting(SimpleMathSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader, "*")

    def parseFromFilter(self, f):
        obj = MultSetting(None, self.dim, self.loader)
        obj._val.setValue(f._val)
        return obj


class DevideSetting(SimpleMathSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader, "/")

    def parseFromFilter(self, f):
        obj = DevideSetting(None, self.dim, self.loader)
        obj._val.setValue(f._val)
        return obj


class PowSetting(SimpleMathSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader, "**")

    def parseFromFilter(self, f):
        obj = PowSetting(None, self.dim, self.loader)
        obj._val.setValue(f._val)
        return obj


class RegionSelectWidget(QGridLayout):
    loadClicked = pyqtSignal(object)

    def __init__(self, parent, dim, loader=None):
        super().__init__()
        self.dim = dim
        self.loader = loader
        self.__initLayout(dim, loader)

    def __initLayout(self, dim, loader):
        self.__loadPrev = QPushButton('Load from Graph', clicked=self.__loadFromPrev)
        if loader is None:
            self.loadClicked.connect(self.__load)
        else:
            self.loadClicked.connect(loader)
        self.addWidget(self.__loadPrev, 0, 0)

        self.addWidget(QLabel("from"), 1, 0)
        self.addWidget(QLabel("to"), 2, 0)
        self.start = [QSpinBox() for d in range(dim)]
        self.end = [QSpinBox() for d in range(dim)]
        i = 1
        for s, e in zip(self.start, self.end):
            s.setRange(0, 10000)
            e.setRange(0, 10000)
            self.addWidget(QLabel("Axis" + str(i)), 0, i)
            self.addWidget(s, 1, i)
            self.addWidget(e, 2, i)
            i += 1

    def __loadFromPrev(self, arg):
        self.loadClicked.emit(self)

    def __load(self, obj):
        c = Graph.active().canvas
        if c is not None:
            r = c.SelectedRange()
            w = c.getWaveData()[0].wave
            p1 = w.posToPoint(r[0])
            p2 = w.posToPoint(r[1])
            self.setRegion(0, (p1[0], p2[0]))
            self.setRegion(1, (p1[1], p2[1]))

    def setRegion(self, axis, range):
        if axis < len(self.start):
            self.start[axis].setValue(min(range[0], range[1]))
            self.end[axis].setValue(max(range[0], range[1]))

    def getRegion(self):
        return [[s.value(), e.value()] for s, e in zip(self.start, self.end)]


class InterpSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self._vals = []
        self._layout = QGridLayout()
        for d in range(dim):
            self._layout.addWidget(QLabel("Axis" + str(d + 1)), 0, d)
            v = QSpinBox()
            v.setRange(0, 100000)
            self._vals.append(v)
            self._layout.addWidget(v, 1, d)
        self.setLayout(self._layout)

    def GetFilter(self):
        size = [v.value() for v in self._vals]
        return InterpFilter(size)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, InterpFilter):
            return True

    def parseFromFilter(self, f):
        obj = InterpSetting(None, self.dim, self.loader)
        for v, s in zip(obj._vals, f._size):
            v.setValue(s)
        return obj


class NormalizeSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self.__parent = parent
        self.range = RegionSelectWidget(self, dim, loader)
        self.combo = QComboBox()
        self.combo.addItem("Whole")
        for d in range(dim):
            self.combo.addItem("Axis" + str(d + 1))

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel("Axis"))
        vbox.addWidget(self.combo)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addLayout(self.range)
        self.setLayout(hbox)

    def GetFilter(self):
        return NormalizeFilter(self.range.getRegion(), self.combo.currentIndex() - 1)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, NormalizeFilter):
            return True

    def parseFromFilter(self, f):
        obj = NormalizeSetting(None, self.dim, self.loader)
        region, axis = f.getParams()
        obj.combo.setCurrentIndex(axis + 1)
        for i, r in enumerate(region):
            obj.range.setRegion(i, r)
        return obj

class ReduceSizeSetting(FilterSettingBase):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(parent, dimension, loader)
        self._layout = _kernelSizeLayout(dimension, odd = False)
        self.setLayout(self._layout)

    def GetFilter(self):
        return ReduceSizeFilter(self._layout.getKernelSize())

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, ReduceSizeFilter):
            return True

    def parseFromFilter(self, f):
        obj = ReduceSizeSetting(None, self.dim, self.loader)
        obj._layout.setKernelSize(f.getKernel())
        return obj

class SelectRegionSetting(FilterSettingBase):
    def __init__(self, parent, dim, loader=None):
        super().__init__(parent, dim, loader)
        self.__parent = parent
        self.range = RegionSelectWidget(self, dim, loader)
        self.setLayout(self.range)

    @classmethod
    def _havingFilter(cls, f):
        if isinstance(f, SelectRegionFilter):
            return True

    def GetFilter(self):
        return SelectRegionFilter(self.range.getRegion())

    def parseFromFilter(self, f):
        obj = SelectRegionSetting(None, self.dim, self.loader)
        region = f.getRegion()
        for i, r in enumerate(region):
            obj.range.setRegion(i, r)
        return obj


class FiltersGUI(QWidget):
    def __init__(self, dimension=2, regionLoader=None):
        super().__init__()
        self._flist = []
        self.loader = regionLoader
        self.dim = dimension
        self.__initLayout()

    def setDimension(self, dimension):
        if self.dim != dimension:
            self.dim = dimension
            self.clear()

    def clear(self):
        while(len(self._flist) > 1):
            self._delete(self._flist[0])
        self._flist[0].clear(dimension=self.dim)

    def GetFilters(self):
        res = []
        for f in self._flist:
            filt = f.GetFilter()
            if filt is not None:
                res.append(filt)
        return Filters(res)

    def __initLayout(self):
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        self._layout = QVBoxLayout()
        self._layout.addStretch()
        self._addFirst()
        inner = QWidget()
        inner.setLayout(self._layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        hbox.addWidget(scroll, 3)

        save = QPushButton("Save", clicked=self._save)
        load = QPushButton("Load", clicked=self._load)
        clear = QPushButton("Clear", clicked=self.clear)
        hbox2 = QHBoxLayout()
        hbox2.addWidget(save)
        hbox2.addWidget(load)
        hbox2.addWidget(clear)

        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)

        self.setLayout(vbox)

    def _addFirst(self):
        first = PreFilterSetting(self, self.dim, self.loader)
        first.filterAdded.connect(self._add)
        first.filterDeleted.connect(self._delete)
        self._flist.append(first)
        self._layout.insertWidget(0, first)

    def _add(self, item):
        if self._flist[len(self._flist) - 1] == item:
            newitem = PreFilterSetting(self, self.dim, self.loader)
            newitem.filterAdded.connect(self._add)
            newitem.filterDeleted.connect(self._delete)
            self._layout.insertWidget(self._layout.count() - 1, newitem)
            self._flist.append(newitem)

    def _delete(self, item, force=False):
        if len(self._flist) > 1 or force:
            self._layout.removeWidget(item)
            item.deleteLater()
            self._flist.remove(item)

    def _save(self):
        self.saveAs("test.fil")

    def _load(self):
        self.loadFrom("test.fil")

    def saveAs(self, file):
        filt = self.GetFilters()
        s = String(file)
        s.data = str(filt)

    def loadFrom(self, file):
        s = String(file)
        self.loadFromString(s.data)

    def loadFromString(self, str):
        self.loadFilters(Filters.fromString(str))

    def loadFilters(self, filt):
        self.clear()
        for f in filt.getFilters():
            self._flist[len(self._flist) - 1].SetFilter(f)


class FiltersDialog(QDialog):
    def __init__(self, dim):
        super().__init__()

        self.filters = FiltersGUI(dim)

        self.ok = QPushButton("O K", clicked=self._ok)
        self.cancel = QPushButton("CANCEL", clicked=self._cancel)
        h1 = QHBoxLayout()
        h1.addWidget(self.ok)
        h1.addWidget(self.cancel)

        layout = QVBoxLayout()
        layout.addWidget(self.filters)
        layout.addLayout(h1)
        self.setLayout(layout)
        self.adjustSize()

    def _ok(self):
        self.ok = True
        self.close()

    def _cancel(self):
        self.ok = False
        self.close()

    def getResult(self):
        return self.ok, self.filters.GetFilters()

    def setFilter(self, filt):
        self.filters.loadFilters(filt)


filterGroups = {
    '': DeleteSetting,
    'Select region': SelectRegionSetting,
    'Smoothing Filter': SmoothingSetting,
    'Frequency Filter': FrequencySetting,
    'Differential Filter': DifferentialSetting,
    'Fourier Filter': FourierSetting,
    'Symmetric Operations': SymmetricOperationSetting,
    'Simple Math': SimpleMathSetting,
    'Interpolation (Only for post process)': InterpSetting,
    'Normalization': NormalizeSetting,
    'Reduce size': ReduceSizeSetting
}
