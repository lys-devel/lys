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
        self._pre = PrefilterTab(self._loadRegion)
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
            self.wave=Wave(fname)
            self.__file.setText(fname)
            self._pre.setWave(self.wave)
    def _loadRegion(self,obj):
        g=Graph.active()
        c=g.canvas
        if c is not None:
            r = c.SelectedRange()
            w=c.getWaveData()[0].wave
            p1 = w.posToPoint(r[0])
            p2 = w.posToPoint(r[1])
            axes=self._cut.findAxisFromGraph(g)
            obj.setRegion(axes[0],(p1[0],p2[0]))
            obj.setRegion(axes[1],(p1[1],p2[1]))

class PrefilterTab(QWidget):
    filterApplied = pyqtSignal(object)
    def __init__(self,loader):
        super().__init__()
        self.__initlayout__(loader)
        self.wave=None
    def __initlayout__(self,loader):
        self.layout=QVBoxLayout()

        self.filt = FiltersGUI(regionLoader=loader)
        self.layout.addWidget(self.filt)
        self.layout.addWidget(QPushButton("Apply filters",clicked=self._click))

        self.setLayout(self.layout)
        self.adjustSize()
    def setWave(self,wave):
        self.wave=wave
        self.filt.setDimension(self.wave.data.ndim)
    def _click(self):
        f=self.filt.GetFilters()
        waves=DaskWave(self.wave)
        f.execute(waves)
        waves.data.compute()
        self.filterApplied.emit(waves)

class ControlledObjectsModel(QAbstractItemModel):
    def __init__(self,obj):
        super().__init__()
        self.obj=obj
        obj.appended.connect(self.layoutChanged.emit)
        obj.removed.connect(self.layoutChanged.emit)
        self.setHeaderData(0,Qt.Horizontal,'Name')
        self.setHeaderData(1,Qt.Horizontal,'Axes')
    def data(self, index, role):
        if not index.isValid() or not role == Qt.DisplayRole:
            return QVariant()
        item = index.internalPointer()
        if item is not None:
            if index.column() == 0:
                return item.Name()
            elif index.column() == 1:
                return str(item)
    def rowCount(self,parent):
        if parent.isValid():
            return 0
        return len(self.obj)
    def columnCount(self,parent):
        return 2
    def index(self,row,column,parent):
        if not parent.isValid():
            return self.createIndex(row,column,self.obj[row][column])
        return QModelIndex()
    def parent(self,index):
        return QModelIndex()
    def headerData(self,section,orientation,role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return "Name"
            else:
                return "Axes"

class controlledWavesGUI(QTreeView):
    def __init__(self,obj,dispfunc,appendfunc):
        super().__init__()
        self.obj=obj
        self.disp=dispfunc
        self.apnd=appendfunc
        self.__model=ControlledObjectsModel(obj)
        self.setModel(self.__model)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
    def buildContextMenu(self):
        menu = QMenu(self)
        menu.addAction(QAction("Display",self,triggered=self._display))
        menu.addAction(QAction("Append",self,triggered=self._append))
        menu.addAction(QAction("Remove",self,triggered=self._remove))
        menu.exec_(QCursor.pos())
    def _display(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.disp(*self.obj[i])
    def _append(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.apnd(*self.obj[i])
    def _remove(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.obj.removeAt(i)
class controlledGraphsGUI(QTreeView):
    def __init__(self,obj):
        super().__init__()
        self.obj=obj
        self.__model=ControlledObjectsModel(obj)
        self.setModel(self.__model)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
    def buildContextMenu(self):
        menu = QMenu(self)
        menu.addAction(QAction("Remove",self,triggered=self._remove))
        menu.exec_(QCursor.pos())
    def _remove(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.obj.removeAt(i)
class controlledExecutorsGUI(QTreeView):
    def __init__(self,obj):
        super().__init__()
        self.obj=obj
        self.__model=ControlledObjectsModel(obj)
        self.setModel(self.__model)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
    def buildContextMenu(self):
        menu = QMenu(self)
        menu.addAction(QAction("Remove",self,triggered=self._remove))
        menu.exec_(QCursor.pos())
    def _remove(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.obj.removeAt(i)
class CutTab(QWidget):
    class _axisLayout(QWidget):
        def __init__(self, dim):
            super().__init__()
            self.__initlayout(dim)
        def __initlayout(self, dim):
            self.grp1=QButtonGroup(self)
            self.grp2=QButtonGroup(self)
            self._btn1=[QRadioButton(str(d)) for d in range(dim)]
            self._btn2=[QRadioButton(str(d)) for d in range(dim)]
            self._btn2.insert(0,QRadioButton("None"))
            self._btn1.append(QRadioButton("Line"))
            self._btn2.append(QRadioButton("Line"))
            self._cmb1=QComboBox()
            self._cmb2=QComboBox()
            layout = QGridLayout()
            layout.addWidget(QLabel("1st Axis"),0,0)
            layout.addWidget(QLabel("2nd Axis"),1,0)
            for i, b in enumerate(self._btn1):
                self.grp1.addButton(b)
            for i, b in enumerate(self._btn1):
                layout.addWidget(b,0,i+2)
            layout.addWidget(self._cmb1,0,len(self._btn1)+2)
            for i, b in enumerate(self._btn2):
                self.grp2.addButton(b)
            for i, b in enumerate(self._btn2):
                layout.addWidget(b,1,i+1)
            layout.addWidget(self._cmb2,1,len(self._btn2)+1)
            self.setLayout(layout)
        def getAxes(self):
            ax1=self._btn1.index(self.grp1.checkedButton())
            ax2=self._btn2.index(self.grp2.checkedButton())-1
            if ax2 == len(self._btn2):
                print("line: not implemented.")
                ax2 = -1
            if ax2 == -1:
                return (ax1,)
            else:
                return (ax1,ax2)
    def __init__(self):
        super().__init__()
        self.graphs=controlledObjects()
        self.waves=controlledObjects()
        self.__exe=ExecutorList()
        self.__initlayout__()
        self.ax=None
        self.wave=None
        self.__exe.updated.connect(self.update)
    def __initlayout__(self):
        self.wlist=controlledWavesGUI(self.waves,self.display,self.append)
        self.glist=controlledGraphsGUI(self.graphs)
        disp=QPushButton("Display",clicked=self.display)
        make=QPushButton("Make",clicked=self.make)

        hbox=QHBoxLayout()
        hbox.addWidget(make)
        hbox.addWidget(disp)
        hbox2=QHBoxLayout()
        hbox2.addWidget(self.wlist)
        hbox2.addWidget(self.glist)
        self._make=QVBoxLayout()
        self._make.addLayout(hbox2)
        self._make.addLayout(hbox)

        self.layout=QVBoxLayout()
        make=QGroupBox("Waves & Graphs")
        make.setLayout(self._make)
        grp=self.__interactive()
        self.layout.addWidget(make)
        self.layout.addWidget(grp)
        self.layout.addStretch()

        self.setLayout(self.layout)
        self.adjustSize()
    def __interactive(self):
        lx=QPushButton("Line (X)",clicked=self._linex)
        ly=QPushButton("Line (Y)",clicked=self._liney)
        rx=QPushButton("Region (X)",clicked=self._regx)
        ry=QPushButton("Region (Y)",clicked=self._regy)
        pt=QPushButton("Point",clicked=self._point)
        rt=QPushButton("Rect",clicked=self._rect)
        cc=QPushButton("Circle",clicked=self._circle)
        li=QPushButton("Free Line",clicked=self._line)
        grid=QGridLayout()
        grid.addWidget(lx,0,0)
        grid.addWidget(ly,0,1)
        grid.addWidget(rx,1,0)
        grid.addWidget(ry,1,1)
        grid.addWidget(pt,2,0)
        grid.addWidget(rt,2,1)
        grid.addWidget(cc,3,0)
        grid.addWidget(li,3,1)

        self.elist=controlledExecutorsGUI(self.__exe)
        hbox=QHBoxLayout()
        hbox.addLayout(grid)
        hbox.addWidget(self.elist)
        grp=QGroupBox("Interactive")
        grp.setLayout(hbox)
        return grp
    def _setWave(self,wave):
        self.wave=wave
        self.__resetLayout()
    def __resetLayout(self):
        if self.ax is not None:
            self._make.removeWidget(self.ax)
            self.ax.deleteLater()
        self.ax = self._axisLayout(self.wave.data.ndim)
        self._make.insertWidget(1,self.ax)
        self.adjustSize()
    def findAxisFromGraph(self, graph):
        return self.graphs.getAxes(graph)
    def make(self,axes=None):
        if not hasattr(axes,"__iter__"):
            if self.ax is None:
                return
            ax=self.ax.getAxes()
        else:
            ax=axes
        if len(ax) in [1,2]:
            w=self.__exe.makeWave(self.wave,ax)
            self.waves.append(w,ax)
            return w
        else:
            return None
    def display(self,wave=None,axes=None):
        if not hasattr(axes,"__iter__"):
            ax=self.ax.getAxes()
        else:
            ax=axes
        if not isinstance(wave,Wave):
            w=self.make(ax)
        else:
            w=wave
        if w is not None:
            g=display(w)
            self.graphs.append(g,ax)
            g.closed.connect(self.graphs.remove)
    def append(self,wave,axes):
        g=Graph.active()
        g.Append(wave)
    def update(self,index):
        for w, axs in self.waves.getObjectsAndAxes():
            if not index in axs:
                w.data=self.__exe.makeWave(self.wave,axs).data
    def _point(self):
        g=Graph.active()
        id=g.canvas.addCross([0,0])
        e=PointExecutor(self.graphs.getAxes(g))
        self.__exe.append(e)
        g.canvas.addCallback(id,e.callback)
    def _rect(self):
        g=Graph.active()
        id=g.canvas.addRect([0,0],[1,1])
        e=RegionExecutor(self.graphs.getAxes(g))
        self.__exe.append(e)
        g.canvas.addCallback(id,e.callback)
    def _circle(self):
        pass
    def _line(self):
        pass
    def _regx(self):
        g=Graph.active()
        id=g.canvas.addRegion([0,1])
        e=RegionExecutor(self.graphs.getAxes(g)[0])
        self.__exe.append(e)
        g.canvas.addCallback(id,e.callback)
    def _regy(self):
        g=Graph.active()
        id=g.canvas.addRegion([0,1],"horizontal")
        e=RegionExecutor(self.graphs.getAxes(g)[1])
        self.__exe.append(e)
        g.canvas.addCallback(id,e.callback)
    def _linex(self):
        g=Graph.active()
        id=g.canvas.addInfiniteLine(0)
        e=PointExecutor(self.graphs.getAxes(g)[0])
        self.__exe.append(e)
        g.canvas.addCallback(id,e.callback)
    def _liney(self):
        g=Graph.active()
        id=g.canvas.addInfiniteLine(0,'horizontal')
        e=PointExecutor(self.graphs.getAxes(g)[0])
        self.__exe.append(e)
        g.canvas.addCallback(id,e.callback)

def create():
    win=MultiCut()

addMainMenu(['Analysis','MultiCut'],create)
