from ExtendAnalysis import *
from .MultiCut import *
from .filtersGUI import *

class MultiCut(AnalysisWindow):
    def __init__(self):
        super().__init__("Multi-dimensional analysis")
        self.__initlayout__()
        self.wave=None
        self.axes=[]
        self.ranges=[]
    def __initlayout__(self):
        self._pre = PrefilterTab()
        self._cut = CutTab()
        self._pre.filterApplied.connect(self._cut._setWave)
        tab = QTabWidget()
        tab.addTab(self._pre,"Prefilter")
        tab.addTab(self._cut,"Cut")

        self.__file=QLineEdit()
        btn=QPushButton("Load",clicked=self.load)

        h1=QHBoxLayout()
        h1.addWidget(btn)
        h1.addWidget(self.__file)

        self.layout=QVBoxLayout()
        self.layout.addWidget(tab)
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
            self._pre.setWave(self.wave)

class PrefilterTab(QWidget):
    filterApplied = pyqtSignal(object)
    def __init__(self):
        super().__init__()
        self.__initlayout__()
        self.wave=None
    def __initlayout__(self):
        self.layout=QVBoxLayout()

        self.filt = FiltersGUI()
        self.layout.addWidget(self.filt)
        self.layout.addWidget(QPushButton("Apply filters",clicked=self._click))

        self.setLayout(self.layout)
        self.adjustSize()
    def setWave(self,wave):
        self.wave=wave
        self.filt.setDimension(self.wave.data.ndim)
    def _click(self):
        f=self.filt.GetFilters()
        f.execute(self.wave)
        w=self.wave.toWave()
        dw=DaskWave(w)
        self.filterApplied.emit(dw)

class CutTab(QWidget):
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
        super().__init__()
        self.__initlayout__()
        self.wave=None
        self.axes=[]
        self.ranges=[]
        self.graphs=self.controlledGraphs()
        self.__exe=ExecutorList()
        self.__exe.updated.connect(self.update)
    def __initlayout__(self):
        disp=QPushButton("Display",clicked=self.display)
        lx=QPushButton("Line (X)",clicked=self._linex)
        ly=QPushButton("Line (Y)",clicked=self._liney)
        rx=QPushButton("Region (X)",clicked=self._regx)
        ry=QPushButton("Region (Y)",clicked=self._regy)
        pt=QPushButton("Point",clicked=self._point)
        rt=QPushButton("Rect",clicked=self._rect)
        cc=QPushButton("Circle",clicked=self._circle)

        hbtn=QHBoxLayout()
        hbtn.addWidget(lx)
        hbtn.addWidget(ly)
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

        self.layout=QVBoxLayout()
        self.layout.addWidget(grp)

        self.setLayout(self.layout)
        self.adjustSize()
    def _setWave(self,wave):
        self.wave=wave
        self.__resetLayout()

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
    def __getChecked(self):
        checked=[]
        for i in range(len(self.wave.shape())):
            if self.axes[i].isChecked():
                checked.append(i)
        return checked
    def __resetLayout(self):
        for i in range(len(self.wave.shape())):
            wid=self._axisWidget(i)
            self.axes.append(wid)
            self.ranges.append([None])
            self.layout.insertWidget(i,wid)
            self.adjustSize()
    def update(self,index):
        for g, axs in self.graphs.getGraphsAndAxes():
            if not index in axs:
                w=g.canvas.getWaveData()[0].wave
                w.data=self.__exe.makeWave(self.wave,axs).data
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
    def _linex(self):
        g=Graph.active()
        id=g.canvas.addInfiniteLine(0)
        e=PointExecutor(self.graphs.graphAxes(g)[0])
        self.__exe.add(e)
        g.canvas.addCallback(id,e.callback)
    def _liney(self):
        g=Graph.active()
        id=g.canvas.addInfiniteLine(0,'horizontal')
        e=PointExecutor(self.graphs.graphAxes(g)[0])
        self.__exe.add(e)
        g.canvas.addCallback(id,e.callback)

def create():
    win=MultiCut()

addMainMenu(['Analysis','MultiCut'],create)
