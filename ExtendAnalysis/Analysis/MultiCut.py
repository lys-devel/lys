from ExtendAnalysis import *
from dask.array.core import Array as DArray
import dask.array as da

class DaskWave(object):
    def __init__(self,wave,axes=None,chunks=64):
        if isinstance(wave,Wave):
            self.__fromWave(wave,axes,chunks)
        elif isinstance(wave,DArray):
            self.__fromda(wave,axes,chunks)
    def __fromWave(self,wave,axes,chunks):
        self.data=da.from_array(wave.data,chunks=chunks)
        if axes is None:
            self.axes=wave.axes
        else:
            self.axes=axes
    def toWave(self):
        w=Wave()
        w.data=self.data.compute()
        w.axes=self.axes
        return w
    def __fromda(self,wave,axes,chunks):
        self.data=wave
        self.axes=axes
    def shape(self):
        return self.data.shape
    def sum(self,axis):
        data=self.data.sum(axis)
        axes=[]
        for i, ax in enumerate(self.axes):
            if not i == axis:
                axes.append(ax)
        return DaskWave(data,axes=axes)
    def __getitem__(self,key):
        if isinstance(key,tuple):
            data=self.data[key]
            axes=[]
            for s, ax in zip(key,self.axes):
                axes.append(self.axes)
            return DaskWave(data,axes=axes)

class AllExecutor(object):
    def __init__(self,axis):
        self.axis=axis
    def getAxes(self):
        return [self.axis]
    def execute(self,wave,axis_offset,ignore=[]):
        if self.axis in ignore:
            return wave, 0
        else:
            return wave.sum(self.axis-axis_offset), 1
class RectExecutor(object):
    def __init__(self,axes,range):
        self.axes=axes
        self.setRange(range)
    def getAxes(self):
        return self.axes
    def setRange(self,range):
        self.range=[]
        for r in range:
            self.range.append(slice(*range))
    def execute(self,wave,axis_offset,ignore=[]):
        off=0
        tmp = wave
        for i, r in enumerate(self.axes,self.range):
            if not i in ignore:
                sl = [slice(None)]*tmp.data.ndim
                sl[i] = r
                off += 1
                tmp = tmp[tuple(sl)].sum(i-axis_offset-off)
        return tmp, off

class MultiCut(AnalysisWindow):
    class controlledGraphs(object):
        def __init__(self):
            self.__graphs=[]
            self.__graphAxis=[]
        def append(self,graph,axes):
            self.__graphs.append(graph)
            self.__graphAxis.append(axes)
            g.closed.connect(self.__graphClosed)
        def __graphClosed(self,graph):
            i=self.__graphs.index(graph)
            self.__graphs.pop(i)
            self.__graphAxis.pop(i)
    class _axisWidget(QWidget):
        valueChanged=pyqtSignal(object,object)
        def __init__(self, n):
            super().__init__()
            self.__initlayout(n)
        def __initlayout(self, n):
            self._check=QCheckBox("Axis "+str(n))
            self._type=QComboBox()
            self._type.addItems(["All", "Point", "Rect", "Circle"])

            h1=QHBoxLayout()
            h1.addWidget(self._check)
            h1.addWidget(self._type)

            h2=QHBoxLayout()
            self.v1=QSpinBox()
            self.v2=QSpinBox()
            self.v1.setRange(0,10000000)
            self.v2.setRange(0,10000000)
            h2.addWidget(self.v1)
            h2.addWidget(self.v2)
            self.layout=QVBoxLayout()
            self.layout.addLayout(h1)
            self.layout.addLayout(h2)
            self.setLayout(self.layout)
        def isChecked(self):
            return self._check.isChecked()
        def setRect(self,index):
            self.index=index
            self._type.setCurrentText("Rect")
        def callback(self,roi):
            index=self.index
            val=self,roi.pos()+roi.size()
            self.v1.setValue(roi.pos()[index])
            self.v2.setValue(roi.pos()[index]+roi.size()[index])
            self.valueChanged.emit(self,(self.v1.value(),self.v2.value()))
    def __init__(self):
        super().__init__("Multi-dimensional analysis")
        self.__initlayout__()
        self.wave=None
        self.axes=[]
        self.ranges=[]
        self.graphs=self.controlledGraphs()
        self.__executors=[]
    def __initlayout__(self):
        disp=QPushButton("Display",clicked=self.display)
        rx=QPushButton("Region (X)",clicked=self._regx)
        ry=QPushButton("Region (Y)",clicked=self._regy)
        pt=QPushButton("Point",clicked=self._point)
        rt=QPushButton("Rect",clicked=self._rect)
        cc=QPushButton("Circle",clicked=self._circle)

        hbtn=QHBoxLayout()
        hbtn.addWidget(rx)
        hbtn.addWidget(ry)
        hbtn.addWidget(pt)
        hbtn.addWidget(rt)
        hbtn.addWidget(cc)
        vbtn=QVBoxLayout()
        vbtn.addWidget(disp)
        vbtn.addLayout(hbtn)

        grp=QGroupBox("Interactive")
        grp.setLayout(vbtn)

        self.__file=QLineEdit()
        btn=QPushButton("Load",clicked=self.load)

        h1=QHBoxLayout()
        h1.addWidget(btn)
        h1.addWidget(self.__file)

        self.layout=QVBoxLayout()
        self.layout.addWidget(grp)
        self.layout.addLayout(h1)

        wid=QWidget()
        wid.setLayout(self.layout)
        self.setWidget(wid)
        self.adjustSize()
    def load(self,file):
        if file == False:
            fname = QFileDialog.getOpenFileName(self, 'Select data file')[0]
        else:
            fname=file
        if os.path.exists(fname):
            self.wave=DaskWave(Wave(fname))
            self.__file.setText(fname)
            self.__resetLayout()
            self.__executors=[AllExecutor(i) for i in range(self.wave.data.ndim)]
    def __resetLayout(self):
        for i in range(len(self.wave.shape())):
            wid=self._axisWidget(i)
            wid.valueChanged.connect(self.callback)
            self.axes.append(wid)
            self.ranges.append([None])
            self.layout.insertWidget(i,wid)
            self.adjustSize()
    def display(self):
        checked=[]
        for i in range(len(self.wave.shape())):
            if self.axes[i].isChecked():
                checked.append(i)
        if len(checked) in [1,2]:
            g=display(self._makeWave(checked))
            self.graphs.append(g,checked)
        else:
            return
    def _makeWave(self,axes):
        tmp=self.wave
        offset=0
        for e in self.__executors:
            tmp, off = e.execute(tmp,offset,ignore=axes)
            offset += off
        return tmp.toWave()
    def _point(self):
        pass
    def _rect(self):
        g=Graph.active()
        i=self.__graphs.index(g)
        ax=self.__graphAxis[i]
        id=g.canvas.addRect([0,0],[1,1])
        k=0
        for n in ax:
            self.axes[n].setRect(k)
            k+=1
            g.canvas.addCallback(id,self.axes[n].callback)
    def _circle(self):
        pass
    def callback(self,axis,r):
        index=self.axes.index(axis)
        self.ranges[index]=r
        self.update(index)
    def update(self,index):
        for g, axs in zip(self.__graphs,self.__graphAxis):
            if not index in axs:
                w=g.canvas.getWaveData()[0].wave
                w.data=self._int2D(axs)
    def _int2D(self,checked):
        import time
        start=time.time()
        j=0
        sl=[slice(None)]*len(self.wave.shape())
        for i in range(len(self.wave.shape())):
            if not i in checked:
                sl[i]=slice(*self.ranges[i])
        res=self.wave.data[tuple(sl)]
        for i in range(len(self.wave.shape())):
            if i in checked:
                j+=1
            else:
                res=np.sum(res,axis=j)
        print(time.time()-start)
        return res

def create():
    win=MultiCut()
    win.load('/home/smb/data/STEMTest.npz')

addMainMenu(['Analysis','MultiCut'],create)
