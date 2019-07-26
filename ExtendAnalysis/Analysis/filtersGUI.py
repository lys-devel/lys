from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from ExtendAnalysis import *
from .filters import *
import _pickle as cPickle

class PreFilterSetting(QWidget):
    filterAdded=pyqtSignal(QWidget)
    filterDeleted=pyqtSignal(QWidget)
    def __init__(self,dimension=2,loader=None):
        super().__init__()
        self.dim=dimension
        self.loader=loader
        self._layout=QVBoxLayout()
        self._combo=QComboBox()
        self._combo.addItem('')
        for f in filterGroups.keys():
            self._combo.addItem(f)
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
            if text in filterGroups:
                self._setting = filterGroups[text](self,self.dim,loader=self.loader)
            self._layout.addWidget(self._setting)
            self.filterAdded.emit(self)
    def GetFilter(self):
        if self._setting is not None:
            return self._setting.GetFilter()
    def SetFilter(self,filt):
        for setting in filterGroups.values():
            s = setting._parseFromFilter(filt)
            if s is not None:
                print(s)

class SmoothingSetting(QWidget):
    def __init__(self,parent,dimension=2,loader=None):
        super().__init__(parent)
        self.dim=dimension
        self._layout=QHBoxLayout()
        self._combo=QComboBox()
        self._combo.addItem('Median')
        self._combo.addItem('Average')
        self._combo.addItem('Gaussian')
        #self._combo.addItem('Bilateral')
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
            self._setting=MedianSetting(self,self.dim)
        if item=='Average':
            self._setting=AverageSetting(self,self.dim)
        if item=='Gaussian':
            self._setting=GaussianSetting(self,self.dim)
        if item=='Bilateral':
            self._setting=BilateralSetting(self,self.dim)
        if self._setting is not None:
            self._layout.addWidget(self._setting)
    def GetFilter(self):
        if self._setting is not None:
            return self._setting.GetFilter()
    @staticmethod
    def _parseFromFilter(f):
        return MedianSetting._parseFromFilter(f)

class OddSpinBox(QSpinBox):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.setMinimum(1)
        self.setSingleStep(2)
        self.setValue(3)
        self.valueChanged.connect(self.valChanged)
    def valChanged(self,val):
        if val % 2 ==0:
            self.setValue(val-1)
class _kernelSizeLayout(QGridLayout):
    def __init__(self,dimension=2):
        super().__init__()
        self.addWidget(QLabel('Kernel Size'),1,0)
        self._kernels = [OddSpinBox() for d in range(dimension)]
        for i, k in enumerate(self._kernels):
            self.addWidget(QLabel('Axis'+str(i+1)),0,i+1)
            self.addWidget(k,1,i+1)
    def getKernelSize(self):
        return [k.value() for k in self._kernels]
    def setKernelSize(self,val):
        for k, v in zip(self._kernels, val):
            k.setValue(v)
class _kernelSigmaLayout(QGridLayout):
    def __init__(self,dimension=2):
        super().__init__()
        self.addWidget(QLabel('Sigma'),1,0)
        self._kernels = [QDoubleSpinBox() for d in range(dimension)]
        for i, k in enumerate(self._kernels):
            k.setMinimum(0)
            self.addWidget(QLabel('Axis'+str(i+1)),0,i+1)
            self.addWidget(k,1,i+1)
    def getKernelSigma(self):
        return [k.value() for k in self._kernels]

class MedianSetting(QWidget):
    def __init__(self,parent,dimension=2):
        super().__init__(parent)
        self._layout=_kernelSizeLayout(dimension)
        self.setLayout(self._layout)
    def GetFilter(self):
        return MedianFilter(self._layout.getKernelSize())
    @staticmethod
    def _parseFromFilter(f):
        if isinstance(f,MedianFilter):
            obj = MedianSetting(None)
            obj._layout.setKernelSize(f.getKernel())
            return obj
        else:
            return None
class AverageSetting(QWidget):
    def __init__(self,parent,dimension=2):
        super().__init__(parent)
        self._layout=_kernelSizeLayout(dimension)
        self.setLayout(self._layout)
    def GetFilter(self):
        return AverageFilter(self._layout.getKernelSize())
class GaussianSetting(QWidget):
    def __init__(self,parent,dimension=2):
        super().__init__(parent)
        self._layout=_kernelSigmaLayout(dimension)
        self.setLayout(self._layout)
    def GetFilter(self):
        return GaussianFilter(self._layout.getKernelSigma())
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

class AxisCheckLayout(QHBoxLayout):
    def __init__(self,dim):
        super().__init__()
        self._axes=[QCheckBox("Axis"+str(i)) for i in range(dim)]
        for a in self._axes:
            self.addWidget(a)
    def GetChecked(self):
        axes = []
        for i, a in enumerate(self._axes):
            if a.isChecked():
                axes.append(i)
        return axes
class FrequencySetting(QWidget):
    def __init__(self,parent,dim=2,loader=None):
        super().__init__(parent)
        self.dim=dim
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
            self._setting=LowPassSetting(self,self.dim)
        if item=='High-pass':
            self._setting=HighPassSetting(self,self.dim)
        if item=='Band-pass':
            self._setting=BandPassSetting(self,self.dim)
        if item=='Band-stop':
            self._setting=BandStopSetting(self,self.dim)
        if self._setting is not None:
            self._layout.addWidget(self._setting)
    def GetFilter(self):
        if self._setting is not None:
            return self._setting.GetFilter()
    @staticmethod
    def _parseFromFilter(f):
        return None
class LowPassSetting(QWidget):
    def __init__(self,parent,dim):
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

        self._axes=AxisCheckLayout(dim)
        vbox=QVBoxLayout()
        vbox.addLayout(self._layout)
        vbox.addLayout(self._axes)
        self.setLayout(vbox)
    def GetFilter(self):
        return LowPassFilter(self._order.value(),self._cut.value(),self._axes.GetChecked())
class HighPassSetting(QWidget):
    def __init__(self,parent,dim):
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
        self._axes=AxisCheckLayout(dim)
        vbox=QVBoxLayout()
        vbox.addLayout(self._layout)
        vbox.addLayout(self._axes)
        self.setLayout(vbox)
    def GetFilter(self):
        return HighPassFilter(self._order.value(),self._cut.value(),self._axes.GetChecked())
class BandPassSetting(QWidget):
    def __init__(self,parent,dim):
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
        self._axes=AxisCheckLayout(dim)
        vbox=QVBoxLayout()
        vbox.addLayout(self._layout)
        vbox.addLayout(self._axes)
        self.setLayout(vbox)
    def GetFilter(self):
        return BandPassFilter(self._order.value(),[self._cut1.value(),self._cut2.value()],self._axes.GetChecked())
class BandStopSetting(QWidget):
    def __init__(self,parent,dim):
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
        self._axes=AxisCheckLayout(dim)
        vbox=QVBoxLayout()
        vbox.addLayout(self._layout)
        vbox.addLayout(self._axes)
        self.setLayout(vbox)
    def GetFilter(self):
        return BandStopFilter(self._order.value(),[self._cut1.value(),self._cut2.value()],self._axes.GetChecked())

class DifferentialSetting(QWidget):
    def __init__(self,parent,dim,loader=None):
        super().__init__(parent)
        self.dim=dim
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
            self._setting=PrewittSetting(self,self.dim)
        if item=='Sobel':
            self._setting=SobelSetting(self,self.dim)
        if item=='Laplacian':
            self._setting=LaplacianSetting(self,self.dim)
        if item=='Sharpen':
            self._setting=SharpenSetting(self,self.dim)
        if self._setting is not None:
            self._layout.addWidget(self._setting)
    def GetFilter(self):
        if self._setting is not None:
            return self._setting.GetFilter()
    @staticmethod
    def _parseFromFilter(f):
        return None

class PrewittSetting(QWidget):
    def __init__(self,parent,dim):
        super().__init__(parent)
        self._layout=AxisCheckLayout(dim)
        self.setLayout(self._layout)
    def GetFilter(self):
        return PrewittFilter(self._layout.GetChecked())
class SobelSetting(QWidget):
    def __init__(self,parent,dim):
        super().__init__(parent)
        self._layout=AxisCheckLayout(dim)
        self.setLayout(self._layout)
    def GetFilter(self):
        return SobelFilter(self._layout.GetChecked())
class LaplacianSetting(QWidget):
    def __init__(self,parent,dim):
        super().__init__(parent)
        self._layout=AxisCheckLayout(dim)
        self.setLayout(self._layout)
    def GetFilter(self):
        return LaplacianFilter(self._layout.GetChecked())
class SharpenSetting(QWidget):
    def __init__(self,parent,dim):
        super().__init__(parent)
        self._layout=AxisCheckLayout(dim)
        self.setLayout(self._layout)
    def GetFilter(self):
        return SharpenFilter(self._layout.GetChecked())

class FourierSetting(QWidget):
    def __init__(self,parent,dim,loader=None):
        super().__init__(parent)
        self.dim=dim
        self._layout=QHBoxLayout()
        self._combo=QComboBox()
        self._combo.addItem('Forward')
        self._combo.addItem('Backward')
        self._combo.currentTextChanged.connect(self._update)
        self._layout.addWidget(QLabel('Direction'))
        self._layout.addWidget(self._combo)
        self.setLayout(self._layout)
        self._setting=None
        self._update('Forward')
    def _update(self,item):
        if self._setting is not None:
            self._layout.removeWidget(self._setting)
            self._setting.deleteLater()
            self._setting=None
        if item=='Forward':
            self._setting=FFTSetting(self,self.dim)
        if item=='Backward':
            self._setting=IFFTSetting(self,self.dim)
        if self._setting is not None:
            self._layout.addWidget(self._setting)
    def GetFilter(self):
        if self._setting is not None:
            return self._setting.GetFilter()
    @staticmethod
    def _parseFromFilter(f):
        return None
class FFTSetting(QWidget):
    def __init__(self,parent,dim):
        super().__init__(parent)
        self._layout=AxisCheckLayout(dim)
        self.setLayout(self._layout)
    def GetFilter(self):
        return FourierFilter(self._layout.GetChecked())
class IFFTSetting(QWidget):
    def __init__(self,parent,dim):
        super().__init__(parent)
        self._layout=AxisCheckLayout(dim)
        self.setLayout(self._layout)
    def GetFilter(self):
        return FourierFilter(self._layout.GetChecked(),type="backward")

class RegionSelectWidget(QGridLayout):
    loadClicked=pyqtSignal(object)
    def __init__(self,parent,dim,loader=None):
        super().__init__()
        self.__initLayout(dim,loader)
    def __initLayout(self,dim,loader):
        self.__loadPrev=QPushButton('Load from Graph',clicked=self.__loadFromPrev)
        if loader is None:
            self.loadClicked.connect(self.__load)
        else:
            self.loadClicked.connect(loader)
        self.addWidget(self.__loadPrev,0,0)

        self.addWidget(QLabel("from"),1,0)
        self.addWidget(QLabel("to"),2,0)
        self.start = [QSpinBox() for d in range(dim)]
        self.end = [QSpinBox() for d in range(dim)]
        i = 1
        for s, e in zip(self.start,self.end):
            s.setRange(0,10000)
            e.setRange(0,10000)
            self.addWidget(QLabel("Axis"+str(i)),0,i)
            self.addWidget(s,1,i)
            self.addWidget(e,2,i)
            i += 1
    def __loadFromPrev(self,arg):
        self.loadClicked.emit(self)
    def __load(self,obj):
        c=Graph.active().canvas
        if c is not None:
            r = c.SelectedRange()
            w=c.getWaveData()[0].wave
            p1 = w.posToPoint(r[0])
            p2 = w.posToPoint(r[1])
            self.setRegion(0,(p1[0],p2[0]))
            self.setRegion(1,(p1[1],p2[1]))
    def setRegion(self,axis,range):
        if axis < len(self.start):
            self.start[axis].setValue(min(range[0],range[1]))
            self.end[axis].setValue(max(range[0],range[1]))
    def getRegion(self):
        return [[s.value(), e.value()] for s, e in zip(self.start,self.end)]

class NormalizeSetting(QWidget):
    def __init__(self,parent,dim,loader=None):
        super().__init__()
        self.__parent=parent
        self.range=RegionSelectWidget(self,dim,loader)
        self.combo=QComboBox()
        self.combo.addItem("Whole")
        for d in range(dim):
            self.combo.addItem("Axis" + str(d+1))

        vbox=QVBoxLayout()
        vbox.addWidget(QLabel("Axis"))
        vbox.addWidget(self.combo)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addLayout(self.range)
        self.setLayout(hbox)
    def GetFilter(self):
        return NormalizeFilter(self.range.getRegion(),self.combo.currentIndex()-1)
    @staticmethod
    def _parseFromFilter(f):
        return None

class SelectRegionSetting(QWidget):
    def __init__(self,parent,dim,loader=None):
        super().__init__()
        self.__parent=parent
        self.range=RegionSelectWidget(self,dim,loader)
        self.setLayout(self.range)
    def GetFilter(self):
        return SelectRegionFilter(self.range.getRegion())
    @staticmethod
    def _parseFromFilter(f):
        return None

class FiltersGUI(QWidget):
    def __init__(self,dimension = 2, regionLoader=None):
        super().__init__()
        self._flist=[]
        self.loader=regionLoader
        self.dim=dimension
        self.__initLayout()
    def setDimension(self,dimension):
        if self.dim != dimension:
            self.dim=dimension
            self.clear()
    def clear(self):
        while(len(self._flist)>0):
            self._delete(self._flist[0],force=True)
        self._addFirst()
    def GetFilters(self):
        res=[]
        for f in self._flist:
            filt=f.GetFilter()
            if filt is not None:
                res.append(filt)
        return Filters(res)
    def __initLayout(self):
        vbox = QVBoxLayout()
        hbox=QHBoxLayout()
        self._layout=QVBoxLayout()
        self._layout.addStretch()
        self._addFirst()
        inner = QWidget()
        inner.setLayout(self._layout)
        scroll=QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        hbox.addWidget(scroll,3)

        save = QPushButton("Save",clicked = self._save)
        load = QPushButton("Load",clicked = self._load)
        clear = QPushButton("Clear",clicked = self.clear)
        hbox2 = QHBoxLayout()
        hbox2.addWidget(save)
        hbox2.addWidget(load)
        hbox2.addWidget(clear)

        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)

        self.setLayout(vbox)
    def _addFirst(self):
        first=PreFilterSetting(self.dim,self.loader)
        first.filterAdded.connect(self._add)
        first.filterDeleted.connect(self._delete)
        self._flist.append(first)
        self._layout.insertWidget(0,first)
    def _add(self,item):
        if self._flist[len(self._flist)-1]==item:
            newitem=PreFilterSetting(self.dim,self.loader)
            newitem.filterAdded.connect(self._add)
            newitem.filterDeleted.connect(self._delete)
            self._layout.insertWidget(self._layout.count()-1,newitem)
            self._flist.append(newitem)
    def _delete(self,item,force=False):
        if len(self._flist)>1 or force:
            self._layout.removeWidget(item)
            item.deleteLater()
            self._flist.remove(item)
    def _save(self):
        self.saveAs("test.fil")
    def _load(self):
        self.loadFrom("test.fil")
    def saveAs(self,file):
        filt = self.GetFilters()
        s=String(file)
        s.data = cPickle.dumps(filt)
    def loadFrom(self,file):
        s=String(file)
        filt = cPickle.loads(eval(s.data)).getFilters()
        self.clear()
        for f in filt:
            self._flist[len(self._flist)-1].SetFilter(f)

filterGroups = {
'Select region': SelectRegionSetting,
'Smoothing Filter': SmoothingSetting,
'Frequency Filter': FrequencySetting,
'Differential Filter': DifferentialSetting,
'Fourier Filter': FourierSetting,
'Normalization': NormalizeSetting
}
