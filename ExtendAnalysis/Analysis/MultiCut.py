import copy
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
    def posToPoint(self,pos,axis):
        ax=self.axes[axis]
        if (ax == np.array(None)).all():
            return int(round(pos))
        x0=ax[0]
        x1=ax[len(ax)-1]
        dx=(x1-x0)/(len(ax)-1)
        return int(round((pos-x0)/dx))
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
                axes.append(ax[s])
            return DaskWave(data,axes=axes)
        else:
            super().__getitem__(key)

class ExecutorList(QObject):
    updated = pyqtSignal(tuple)
    def __init__(self):
        super().__init__()
        self.__exe=[]
    def add(self,obj):
        self.__exe.append(obj)
        obj.updated.connect(self.updated.emit)
    def __exeList(self,wave):
        axes=[]
        for e in self.__exe:
            axes.extend(e.getAxes())
        axes=list(set(axes))
        res=list(self.__exe)
        for i in range(wave.data.ndim):
            if not i in axes:
                res.append(AllExecutor(i))
        return res
    def makeWave(self,wave,axes):
        tmp=wave
        offset=0
        for e in self.__exeList(wave):
            tmp, off = e.execute(tmp,offset,ignore=axes)
            offset += off
        return tmp.toWave()
class AllExecutor(QObject):
    updated = pyqtSignal(tuple)
    def __init__(self,axis):
        super().__init__()
        self.axis=axis
    def getAxes(self):
        return [self.axis]
    def execute(self,wave,axis_offset,ignore=[]):
        if self.axis in ignore:
            return wave, 0
        else:
            return wave.sum(self.axis-axis_offset), 1
class RegionExecutor(QObject):
    updated = pyqtSignal(tuple)
    def __init__(self,axes,range=None):
        super().__init__()
        if isinstance(axes,int):
            self.axes=(axes,)
        else:
            self.axes=axes
        if range is not None:
            self.setRange(range)
    def getAxes(self):
        return self.axes
    def setRange(self,range):
        self.range=[]
        if isinstance(range[0],list):
            for r in range:
                self.range.append(r)
        else:
            self.range.append(range)
        self.updated.emit(self.axes)
    def execute(self,wave,axis_offset,ignore=[]):
        off=0
        tmp = wave
        for i, r in zip(self.axes,self.range):
            if not i in ignore:
                sl = [slice(None)]*tmp.data.ndim
                sl[i-axis_offset-off] = slice(wave.posToPoint(r[0],i),wave.posToPoint(r[1],i))
                tmp = tmp[tuple(sl)].sum(i-axis_offset-off)
                off += 1
        return tmp, off
    def callback(self,region):
        self.setRange(region)
class PointExecutor(QObject):
    updated = pyqtSignal(tuple)
    def __init__(self,axes,pos=None):
        super().__init__()
        self.axes=axes
        if pos is not None:
            self.setPosition(pos)
    def getAxes(self):
        return self.axes
    def setPosition(self,pos):
        self.position=pos
        self.updated.emit(self.axes)
    def execute(self,wave,axis_offset,ignore=[]):
        off=0
        tmp = wave
        for i, p in zip(self.axes,self.position):
            if not i in ignore:
                sl = [slice(None)]*tmp.data.ndim
                sl[i-off] = wave.posToPoint(p,i)
                tmp = tmp[tuple(sl)]#.sum(i-axis_offset-off)
                off += 1
        return tmp, off
    def callback(self,pos):
        self.setPosition(pos)

class MultiCut(AnalysisWindow):
    class controlledGraphs(object):
        def __init__(self):
            self.__graphs=[]
            self.__graphAxis=[]
        def append(self,graph,axes):
            self.__graphs.append(graph)
            self.__graphAxis.append(axes)
            graph.closed.connect(self.__graphClosed)
        def __graphClosed(self,graph):
            i=self.__graphs.index(graph)
            self.__graphs.pop(i)
            self.__graphAxis.pop(i)
        def graphAxes(self,graph):
            i=self.__graphs.index(graph)
            return self.__graphAxis[i]
        def getGraphsAndAxes(self):
            return zip(self.__graphs,self.__graphAxis)
    class _axisWidget(QWidget):
        valueChanged=pyqtSignal(object,object)
        def __init__(self, n):
            super().__init__()
            self.__initlayout(n)
        def __initlayout(self, n):
            self._check=QCheckBox("Axis "+str(n))

            h1=QHBoxLayout()
            h1.addWidget(self._check)

            self.layout=QVBoxLayout()
            self.layout.addLayout(h1)
            self.setLayout(self.layout)
        def isChecked(self):
            return self._check.isChecked()
    def __init__(self):
        super().__init__("Multi-dimensional analysis")
        self.__initlayout__()
        self.wave=None
        self.axes=[]
        self.ranges=[]
        self.graphs=self.controlledGraphs()
        self.__exe=ExecutorList()
        self.__exe.updated.connect(self.update)
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
            self.axes.append(wid)
            self.ranges.append([None])
            self.layout.insertWidget(i,wid)
            self.adjustSize()
    def __getChecked(self):
        checked=[]
        for i in range(len(self.wave.shape())):
            if self.axes[i].isChecked():
                checked.append(i)
        return checked
    def display(self,axes=None):
        if not hasattr(axes,"__iter__"):
            ax=self.__getChecked()
        else:
            ax=axes
        if len(ax) in [1,2]:
            w=self.__exe.makeWave(self.wave,ax)
            g=display(w)
            self.graphs.append(g,ax)
        else:
            return
    def _point(self):
        g=Graph.active()
        id=g.canvas.addCross([0,0])
        e=PointExecutor(self.graphs.graphAxes(g))
        self.__exe.add(e)
        g.canvas.addCallback(id,e.callback)
    def _rect(self):
        g=Graph.active()
        id=g.canvas.addRect([0,0],[1,1])
        e=RegionExecutor(self.graphs.graphAxes(g))
        self.__exe.add(e)
        g.canvas.addCallback(id,e.callback)
    def _circle(self):
        pass
    def _regx(self):
        g=Graph.active()
        id=g.canvas.addRegion([0,1])
        e=RegionExecutor(self.graphs.graphAxes(g)[0])
        self.__exe.add(e)
        g.canvas.addCallback(id,e.callback)
    def _regy(self):
        g=Graph.active()
        id=g.canvas.addRegion([0,1],"horizontal")
        e=RegionExecutor(self.graphs.graphAxes(g)[1])
        self.__exe.add(e)
        g.canvas.addCallback(id,e.callback)
    def update(self,index):
        for g, axs in self.graphs.getGraphsAndAxes():
            if not index in axs:
                w=g.canvas.getWaveData()[0].wave
                w.data=self.__exe.makeWave(self.wave,axs).data

def create():
    win=MultiCut()
    win.load('STEMTest.npz')

addMainMenu(['Analysis','MultiCut'],create)
