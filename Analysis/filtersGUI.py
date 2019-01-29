from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from .filters import *

class PreFilterSetting(QWidget):
    filterAdded=pyqtSignal(QWidget)
    filterDeleted=pyqtSignal(QWidget)
    def __init__(self):
        super().__init__()
        self._layout=QVBoxLayout()
        self._combo=QComboBox()
        self._combo.addItem('')
        self._combo.addItem('Select region')
        self._combo.addItem('Smoothing Filter')
        self._combo.addItem('Frequency Filter')
        self._combo.addItem('Differential Filter')
        self._combo.addItem('Normalization')
        self._combo.addItem('Fourier Filter')
        self._combo.currentTextChanged.connect(self._update)
        self._layout.addWidget(QLabel('Type'))
        self._layout.addWidget(self._combo)

        self.setLayout(self._layout)
        self._setting=None
    def _update(self,text):
        if self._setting is not None:
            self._layout.removeWidget(self._setting)
            self._setting.deleteLater()
            self._setting=None
        if text=='':
            self.filterDeleted.emit(self)
        else:
            if text=='Smoothing Filter':
                self._setting=SmoothingSetting(self)
            if text=='Frequency Filter':
                self._setting=FrequencySetting(self)
            if text=='Differential Filter':
                self._setting=DifferentialSetting(self)
            if text=='Normalization':
                self._setting=NormalizeSetting(self)
            if text=='Select region':
                self._setting=SelectRegionSetting(self)
            self._layout.addWidget(self._setting)
            self.filterAdded.emit(self)
    def GetFilter(self):
        if self._setting is not None:
            return self._setting.GetFilter()

class SmoothingSetting(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._layout=QHBoxLayout()
        self._combo=QComboBox()
        self._combo.addItem('Median')
        self._combo.addItem('Average')
        self._combo.addItem('Gaussian')
        self._combo.addItem('Bilateral')
        self._combo.currentTextChanged.connect(self._update)
        self._layout.addWidget(QLabel('Method'))
        self._layout.addWidget(self._combo)
        self.setLayout(self._layout)
        self._setting=None
        self._update('Median')
    def _update(self,item):
        if self._setting is not None:
            self._layout.removeWidget(self._setting)
            self._setting.deleteLater()
            self._setting=None
        if item=='Median':
            self._setting=MedianSetting(self)
        if item=='Average':
            self._setting=AverageSetting(self)
        if item=='Gaussian':
            self._setting=GaussianSetting(self)
        if item=='Bilateral':
            self._setting=BilateralSetting(self)
        if self._setting is not None:
            self._layout.addWidget(self._setting)
    def GetFilter(self):
        if self._setting is not None:
            return self._setting.GetFilter()

class MedianSetting(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._layout=QHBoxLayout()
        self._kernel=QSpinBox()
        self._kernel.setMinimum(3)
        self._layout.addWidget(QLabel('Kernel Size'))
        self._layout.addWidget(self._kernel)
        self.setLayout(self._layout)
    def GetFilter(self):
        return MedianFilter(self._kernel.value())
class AverageSetting(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._layout=QHBoxLayout()
        self._kernel=QSpinBox()
        self._kernel.setMinimum(3)
        self._layout.addWidget(QLabel('Kernel Size'))
        self._layout.addWidget(self._kernel)
        self.setLayout(self._layout)
    def GetFilter(self):
        return AverageFilter(self._kernel.value())
class GaussianSetting(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._layout=QHBoxLayout()
        self._kernel=QSpinBox()
        self._kernel.setMinimum(3)
        self._layout.addWidget(QLabel('Kernel Size'))
        self._layout.addWidget(self._kernel)
        self.setLayout(self._layout)
    def GetFilter(self):
        return GaussianFilter(self._kernel.value())
class BilateralSetting(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._layout=QHBoxLayout()
        self._kernel=QSpinBox()
        self._kernel.setMinimum(3)
        self._kernel.setValue(5)
        self._s_color=QSpinBox()
        self._s_color.setMinimum(1)
        self._s_color.setValue(7)
        self._s_space=QSpinBox()
        self._s_space.setMinimum(1)
        self._s_space.setValue(7)
        self._layout.addWidget(QLabel('Kernel Size'))
        self._layout.addWidget(self._kernel)
        self._layout.addWidget(QLabel('Sigma color'))
        self._layout.addWidget(self._s_color)
        self._layout.addWidget(QLabel('Sigma space'))
        self._layout.addWidget(self._s_space)
        self.setLayout(self._layout)
    def GetFilter(self):
        return BilateralFilter(self._kernel.value(),self._s_color.value(),self._s_space.value())

class FrequencySetting(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._layout=QHBoxLayout()
        self._combo=QComboBox()
        self._combo.addItem('Low-pass')
        self._combo.addItem('High-pass')
        self._combo.addItem('Band-pass')
        self._combo.addItem('Band-stop')
        self._combo.currentTextChanged.connect(self._update)
        self._layout.addWidget(QLabel('Method'))
        self._layout.addWidget(self._combo)
        self.setLayout(self._layout)
        self._setting=None
        self._update('Low-pass')
    def _update(self,item):
        if self._setting is not None:
            self._layout.removeWidget(self._setting)
            self._setting.deleteLater()
            self._setting=None
        if item=='Low-pass':
            self._setting=LowPassSetting(self)
        if item=='High-pass':
            self._setting=HighPassSetting(self)
        if item=='Band-pass':
            self._setting=BandPassSetting(self)
        if item=='Band-stop':
            self._setting=BandStopSetting(self)
        if self._setting is not None:
            self._layout.addWidget(self._setting)
    def GetFilter(self):
        if self._setting is not None:
            return self._setting.GetFilter()
class LowPassSetting(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._layout=QHBoxLayout()
        self._cut=QDoubleSpinBox()
        self._cut.setDecimals(3)
        self._cut.setRange(0,1)
        self._cut.setValue(0.2)
        self._order=QSpinBox()
        self._order.setRange(0,1000)
        self._order.setValue(1)
        self._layout.addWidget(QLabel('Order'))
        self._layout.addWidget(self._order)
        self._layout.addWidget(QLabel('Cutoff'))
        self._layout.addWidget(self._cut)
        self.setLayout(self._layout)
    def GetFilter(self):
        return LowPassFilter(self._order.value(),self._cut.value())
class HighPassSetting(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._layout=QHBoxLayout()
        self._cut=QDoubleSpinBox()
        self._cut.setDecimals(3)
        self._cut.setRange(0,1)
        self._cut.setValue(0.8)
        self._order=QSpinBox()
        self._order.setRange(0,1000)
        self._order.setValue(1)
        self._layout.addWidget(QLabel('Order'))
        self._layout.addWidget(self._order)
        self._layout.addWidget(QLabel('Cutoff'))
        self._layout.addWidget(self._cut)
        self.setLayout(self._layout)
    def GetFilter(self):
        return HighPassFilter(self._order.value(),self._cut.value())
class BandPassSetting(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._layout=QHBoxLayout()
        self._cut1=QDoubleSpinBox()
        self._cut1.setDecimals(3)
        self._cut1.setRange(0,1)
        self._cut1.setValue(0.2)
        self._cut2=QDoubleSpinBox()
        self._cut2.setDecimals(3)
        self._cut2.setRange(0,1)
        self._cut2.setValue(0.8)
        self._order=QSpinBox()
        self._order.setRange(0,1000)
        self._order.setValue(1)
        self._layout.addWidget(QLabel('Order'))
        self._layout.addWidget(self._order)
        self._layout.addWidget(QLabel('Low'))
        self._layout.addWidget(self._cut1)
        self._layout.addWidget(QLabel('High'))
        self._layout.addWidget(self._cut2)
        self.setLayout(self._layout)
    def GetFilter(self):
        return BandPassFilter(self._order.value(),[self._cut1.value(),self._cut2.value()])
class BandStopSetting(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._layout=QHBoxLayout()
        self._cut1=QDoubleSpinBox()
        self._cut1.setDecimals(3)
        self._cut1.setRange(0,1)
        self._cut1.setValue(0.2)
        self._cut2=QDoubleSpinBox()
        self._cut2.setDecimals(3)
        self._cut2.setRange(0,1)
        self._cut2.setValue(0.8)
        self._order=QSpinBox()
        self._order.setRange(0,1000)
        self._order.setValue(1)
        self._layout.addWidget(QLabel('Order'))
        self._layout.addWidget(self._order)
        self._layout.addWidget(QLabel('Low'))
        self._layout.addWidget(self._cut1)
        self._layout.addWidget(QLabel('High'))
        self._layout.addWidget(self._cut2)
        self.setLayout(self._layout)
    def GetFilter(self):
        return BandStopFilter(self._order.value(),[self._cut1.value(),self._cut2.value()])

class DifferentialSetting(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._layout=QHBoxLayout()
        self._combo=QComboBox()
        self._combo.addItem('Prewitt')
        self._combo.addItem('Sobel')
        self._combo.addItem('Laplacian')
        self._combo.addItem('Sharpen')
        self._combo.currentTextChanged.connect(self._update)
        self._layout.addWidget(QLabel('Method'))
        self._layout.addWidget(self._combo)
        self.setLayout(self._layout)
        self._setting=None
        self._update('Prewitt')
    def _update(self,item):
        if self._setting is not None:
            self._layout.removeWidget(self._setting)
            self._setting.deleteLater()
            self._setting=None
        if item=='Prewitt':
            self._setting=PrewittSetting(self)
        if item=='Sobel':
            self._setting=SobelSetting(self)
        if item=='Laplacian':
            self._setting=LaplacianSetting(self)
        if item=='Sharpen':
            self._setting=SharpenSetting(self)
        if self._setting is not None:
            self._layout.addWidget(self._setting)
    def GetFilter(self):
        if self._setting is not None:
            return self._setting.GetFilter()

class PrewittSetting(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._layout=QHBoxLayout()
        self._combo=QComboBox()
        self._combo.addItem('x+y')
        self._combo.addItem('x')
        self._combo.addItem('y')
        self._layout.addWidget(self._combo)
        self.setLayout(self._layout)
    def GetFilter(self):
        return PrewittFilter(self._combo.currentText())
class SobelSetting(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._layout=QHBoxLayout()
        self._combo=QComboBox()
        self._combo.addItem('x+y')
        self._combo.addItem('x')
        self._combo.addItem('y')
        self._layout.addWidget(self._combo)
        self.setLayout(self._layout)
    def GetFilter(self):
        return SobelFilter(self._combo.currentText())
class LaplacianSetting(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._layout=QHBoxLayout()
        self.setLayout(self._layout)
    def GetFilter(self):
        return LaplacianFilter()
class SharpenSetting(QWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self._layout=QHBoxLayout()
        self.setLayout(self._layout)
    def GetFilter(self):
        return SharpenFilter()

class RegionSelectWidget(QGridLayout):
    def __init__(self,parent):
        super().__init__()
        self.__initLayout()
    def __initLayout(self):
        self.__x1=QSpinBox()
        self.__x1.setRange(0,10000)
        self.__x2=QSpinBox()
        self.__x2.setRange(0,10000)
        self.__y1=QSpinBox()
        self.__y1.setRange(0,10000)
        self.__y2=QSpinBox()
        self.__y2.setRange(0,10000)
        self.addWidget(QLabel('Range'),0,0)
        self.__loadPrev=QPushButton('Load from prev.',clicked=self.__loadFromPrev)
        self.addWidget(self.__loadPrev,1,0)
        self.addWidget(QLabel('x1'),0,1)
        self.addWidget(QLabel('x2'),0,2)
        self.addWidget(QLabel('y1'),0,3)
        self.addWidget(QLabel('y2'),0,4)
        self.addWidget(self.__x1,1,1)
        self.addWidget(self.__x2,1,2)
        self.addWidget(self.__y1,1,3)
        self.addWidget(self.__y2,1,4)
    def __loadFromPrev(self,arg):
        from ExtendAnalysis import PreviewWindow
        p=PreviewWindow.SelectedArea()
        if p is None:
            return
        self.__x1.setValue(min(p[0][0],p[1][0]))
        self.__x2.setValue(max(p[0][0],p[1][0]))
        self.__y1.setValue(min(p[0][1],p[1][1]))
        self.__y2.setValue(max(p[0][1],p[1][1]))
    def getRegion(self):
        return [self.__x1.value(),self.__x2.value(),self.__y1.value(),self.__y2.value()]

class NormalizeSetting(QWidget):
    def __init__(self,parent):
        super().__init__()
        self.__parent=parent
        self.__initLayout()
    def GetFilter(self):
        return NormalizeFilter(self.range.getRegion())
    def __initLayout(self):
        self.range=RegionSelectWidget(self)
        self.setLayout(self.range)

class SelectRegionSetting(QWidget):
    def __init__(self,parent):
        super().__init__()
        self.__parent=parent
        self.__initLayout()
    def GetFilter(self):
        return SelectRegionFilter(self.range.getRegion())
    def __initLayout(self):
        self.range=RegionSelectWidget(self)
        self.setLayout(self.range)

class FiltersGUI(QWidget):
    def __init__(self):
        super().__init__()
        self._flist=[]
        self.__initLayout()
    def GetFilters(self):
        res=[]
        for f in self._flist:
            filt=f.GetFilter()
            if filt is not None:
                res.append(filt)
        return Filters(res)
    def __initLayout(self):
        hbox=QHBoxLayout()
        self._layout=QVBoxLayout()
        first=PreFilterSetting()
        first.filterAdded.connect(self._add)
        first.filterDeleted.connect(self._delete)
        self._flist.append(first)

        self._layout.addWidget(first)
        self._layout.addStretch()
        hbox.addLayout(self._layout,3)
        self.setLayout(hbox)
    def _add(self,item):
        if self._flist[len(self._flist)-1]==item:
            newitem=PreFilterSetting()
            newitem.filterAdded.connect(self._add)
            newitem.filterDeleted.connect(self._delete)
            self._layout.insertWidget(self._layout.count()-1,newitem)
            self._flist.append(newitem)
    def _delete(self,item):
        if len(self._flist)>1:
            self._layout.removeWidget(item)
            item.deleteLater()
            self._flist.remove(item)
