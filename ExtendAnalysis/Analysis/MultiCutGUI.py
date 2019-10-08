import copy
from ExtendAnalysis import *
from .MultiCut import *
from .filtersGUI import *

class MultiCut(AnalysisWindow):
    def __init__(self,wave=None):
        super().__init__("Multi-dimensional analysis")
        self.__initlayout__()
        self.wave=None
        self.axes=[]
        self.ranges=[]
        if wave is not None:
            self.load(wave)
    def __initlayout__(self):
        self._pre = PrefilterTab(self._loadRegion)
        self._cut = CutTab()
        self._ani = AnimationTab(self._cut.getExecutorList())
        self._pre.filterApplied.connect(self._cut._setWave)
        self._pre.filterApplied.connect(self._ani._setWave)
        self._ani.updated.connect(self._cut.update)
        tab = QTabWidget()
        tab.addTab(self._pre,"Prefilter")
        tab.addTab(self._cut,"Cut")
        tab.addTab(self._ani,"Animation")

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
        if isinstance(fname,str):
            self.wave=Wave(fname)
            self.__file.setText(fname)
            self._pre.setWave(self.wave)
        elif isinstance(fname,Wave):
            self.wave=fname
            self.__file.setText(self.wave.Name())
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
    class _chunkDialog(QDialog):
        class customSpinBox(QSpinBox):
            def __init__(self,value):
                super().__init__()
                self.setRange(-1,value)
                self.val = value
                self.vallist = self.make_divisors(value)
                self.vallist.insert(0,-1)
                self.setValue(value)
            def stepBy(self, steps):
                pos = self.vallist.index(self.value()) + steps
                if pos < 0:
                    pos = 0
                if pos > len(self.vallist):
                    pos = (self.vallist) - 1
                self.setValue(self.vallist[pos])
            def make_divisors(self,n):
                divisors = []
                for i in range(1, int(n**0.5)+1):
                    if n % i == 0:
                        divisors.append(i)
                        if i != n // i:
                            divisors.append(n//i)
                divisors.sort()
                return divisors
        def __init__(self, size):
            super().__init__(None)

            self.btn1 = QRadioButton("Auto")
            self.btn2 = QRadioButton("Custom")
            self.btn2.setChecked(True)

            self.ok = QPushButton("O K",clicked = self._ok)
            self.cancel = QPushButton("CANCEL", clicked = self._cancel)
            h1 = QHBoxLayout()
            h1.addWidget(self.ok)
            h1.addWidget(self.cancel)

            self.chunks = [self.customSpinBox(i) for i in size]
            h2 = QHBoxLayout()
            for c in self.chunks:
                h2.addWidget(c)

            layout = QVBoxLayout()
            layout.addWidget(self.btn1)
            layout.addWidget(self.btn2)
            layout.addLayout(h2)
            layout.addLayout(h1)
            self.setLayout(layout)
        def _ok(self):
            self.ok = True
            self.close()
        def _cancel(self):
            self.ok = False
            self.close()
        def getResult(self):
            if self.btn1.isChecked():
                return self.ok, "auto"
            else:
                return self.ok, tuple([c.value() for c in self.chunks])

    filterApplied = pyqtSignal(object)
    def __init__(self,loader):
        super().__init__()
        self.__initlayout__(loader)
        self.wave=None
        self.__chunk = "auto"
    def __initlayout__(self,loader):
        self.layout=QVBoxLayout()

        self.filt = FiltersGUI(regionLoader=loader)
        self.layout.addWidget(self.filt)
        h1 = QHBoxLayout()
        h1.addWidget(QPushButton("Rechunk",clicked=self._chunk))
        h1.addWidget(QPushButton("Apply filters",clicked=self._click))
        self.layout.addLayout(h1)

        self.setLayout(self.layout)
        self.adjustSize()
    def setWave(self,wave):
        self.wave=wave
        self.filt.setDimension(self.wave.data.ndim)
    def _click(self):
        f=self.filt.GetFilters()
        waves=DaskWave(self.wave,chunks=self.__chunk)
        f.execute(waves)
        w = waves.toWave()
        dw = DaskWave(w)
        self.filterApplied.emit(dw)
    def _chunk(self):
        if self.wave is None:
            return
        d = self._chunkDialog(self.wave.data.shape)
        d.exec_()
        ok, res = d.getResult()
        if ok:
            self.__chunk = res

class ControlledObjectsModel(QAbstractItemModel):
    def __init__(self,obj):
        super().__init__()
        self.obj=obj
        obj.appended.connect(lambda x: self.layoutChanged.emit())
        obj.removed.connect(lambda x: self.layoutChanged.emit())
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
class ExecutorModel(ControlledObjectsModel):
    def data(self, index, role):
        item = index.internalPointer()
        if item is not None and role == Qt.ForegroundRole:
            if self.obj.isEnabled(index.row()):
                return QBrush(QColor("black"))
            else:
                return QBrush(QColor("gray"))
        return super().data(index,role)
class controlledWavesGUI(QTreeView):
    updated = pyqtSignal()
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
        menu.addAction(QAction("PostProcess",self,triggered=self._post))
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
    def _post(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        w = self.obj[i][0]
        d = FiltersDialog(w.data.ndim)
        if 'MultiCut_PostProcess' in w.note:
            d.setFilter(Filters.fromString(w.note['MultiCut_PostProcess']))
        d.exec_()
        ok, filt = d.getResult()
        if ok:
            w.note['MultiCut_PostProcess']=str(filt)
        self.updated.emit()

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
        self.__model=ExecutorModel(obj)
        self.setModel(self.__model)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
    def buildContextMenu(self):
        menu = QMenu(self)
        menu.addAction(QAction("Setting",self,triggered=self._setting))
        menu.addAction(QAction("Enable",self,triggered=self._enable))
        menu.addAction(QAction("Disable",self,triggered=self._disable))
        menu.addAction(QAction("Remove",self,triggered=self._remove))
        menu.exec_(QCursor.pos())
    def _setting(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.obj.setting(i)
    def _remove(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.obj.removeAt(i)
    def _enable(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.obj.enableAt(i)
    def _disable(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.obj.disableAt(i)

class CutTab(QWidget):
    class _axisLayout(QWidget):
        def __init__(self, dim):
            super().__init__()
            self.__initlayout(dim)
            self._lineids={}
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
        def updateLines(self,lines):
            for c in [self._cmb1, self._cmb2]:
                old=c.currentText()
                for i in range(c.count()):
                    c.removeItem(0)
                for i, l in enumerate(lines):
                    c.addItem(l.Name())
                    if l.Name()==old:
                        c.setCurrentIndex(i)
            self._lineids={}
            for l in lines:
                self._lineids[l.Name()] = l.ID()
        def getAxes(self):
            ax1=self._btn1.index(self.grp1.checkedButton())
            ax2=self._btn2.index(self.grp2.checkedButton())-1
            if ax1 == len(self._btn1)-1:
                ax1 = self._lineids[self._cmb1.currentText()]
            if ax2 == len(self._btn2)-2:
                ax2 = self._lineids[self._cmb2.currentText()]
            if ax2 == -1:
                return (ax1,)
            else:
                return (ax1,ax2)
    def __init__(self):
        super().__init__()
        self.graphs=controlledObjects()
        self.waves=controlledObjects()
        self.lines=controlledObjects()
        self.__exe=ExecutorList()
        self.graphs.removed.connect(self.__exe.graphRemoved)
        self.__initlayout__()
        self.ax=None
        self.wave=None
        self.__exe.updated.connect(self.update)
        self.__exe.appended.connect(self._exechanged)
        self.__exe.removed.connect(self._exechanged)
    def __initlayout__(self):
        self.wlist=controlledWavesGUI(self.waves,self.display,self.append)
        self.wlist.updated.connect(self.updateAll)
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
        make=QGroupBox("Waves & Graphs")
        make.setLayout(self._make)

        grp=self.__interactive()

        self.layout=QVBoxLayout()
        self.layout.addWidget(make)
        self.layout.addWidget(grp)
        self.layout.addStretch()

        self.setLayout(self.layout)
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
        old = self.wave
        self.wave=wave
        print("Wave set. shape = ", self.wave.data.shape, ", dtype = ",self.wave.data.dtype, ", chunksize - ", self.wave.data.chunksize)
        if old is not None:
            if old.data.shape == wave.data.shape:
                self.updateAll()
                return
        self.__resetLayout()
    def __resetLayout(self):
        if self.ax is not None:
            self._make.removeWidget(self.ax)
            self.ax.deleteLater()
        self.ax = self._axisLayout(self.wave.data.ndim)
        self._make.insertWidget(1,self.ax)
        self.adjustSize()
    def _exechanged(self):
        list=self.__exe.getFreeLines()
        self.ax.updateLines(list)
    def getExecutorList(self):
        return self.__exe
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
            g=display(w,lib="pyqtgraph")
            self.graphs.append(g,ax)
            g.closed.connect(self.graphs.remove)
    def append(self,wave,axes):
        g=Graph.active()
        g.Append(wave)
    def updateAll(self):
        for w, axs in self.waves.getObjectsAndAxes():
            try:
                wav=self.__exe.makeWave(self.wave,axs)
                w.axes=wav.axes
                w.data=wav.data
                self._postProcess(w)
            except:
                pass
    def update(self,index,all=False):
        for w, axs in self.waves.getObjectsAndAxes():
            if index[0] < 10000:
                if not set(index).issubset(axs):
                    try:
                        wav=self.__exe.makeWave(self.wave,axs)
                        w.axes=wav.axes
                        w.data=wav.data
                        self._postProcess(w)
                    except:
                        pass
            else:
                if index[0] in axs:
                    try:
                        wav=self.__exe.makeWave(self.wave,axs)
                        w.axes=wav.axes
                        w.data=wav.data
                        self._postProcess(w)
                    except:
                        pass

    def _postProcess(self,w):
        if "MultiCut_PostProcess" in w.note:
            filt = Filters.fromString(w.note["MultiCut_PostProcess"])
            filt.execute(w)
    def _point(self):
        g=Graph.active()
        id=g.canvas.addCross([0,0])
        e=PointExecutor(self.graphs.getAxes(g))
        g.canvas.addCallback(id,e.callback)
        self.__exe.append(e,g)
    def _rect(self):
        g=Graph.active()
        id=g.canvas.addRect([0,0],[1,1])
        e=RegionExecutor(self.graphs.getAxes(g))
        g.canvas.addCallback(id,e.callback)
        self.__exe.append(e,g)
    def _circle(self):
        pass
    def _line(self):
        g=Graph.active()
        id=g.canvas.addLine([[0,0],[1,1]])
        e=FreeLineExecutor(self.graphs.getAxes(g))
        g.canvas.addCallback(id,e.callback)
        self.__exe.append(e,g)
    def _regx(self):
        g=Graph.active()
        id=g.canvas.addRegion([0,1])
        e=RegionExecutor(self.graphs.getAxes(g)[0])
        g.canvas.addCallback(id,e.callback)
        self.__exe.append(e,g)
    def _regy(self):
        g=Graph.active()
        id=g.canvas.addRegion([0,1],"horizontal")
        e=RegionExecutor(self.graphs.getAxes(g)[1])
        g.canvas.addCallback(id,e.callback)
        self.__exe.append(e,g)
    def _linex(self):
        g=Graph.active()
        id=g.canvas.addInfiniteLine(0)
        e=PointExecutor(self.graphs.getAxes(g)[0])
        g.canvas.addCallback(id,e.callback)
        self.__exe.append(e,g)
    def _liney(self):
        g=Graph.active()
        id=g.canvas.addInfiniteLine(0,'horizontal')
        e=PointExecutor(self.graphs.getAxes(g)[0])
        g.canvas.addCallback(id,e.callback)
        self.__exe.append(e,g)

class AnimationTab(QWidget):
    updated=pyqtSignal(int)
    class _axisWidget(QWidget):
        def __init__(self, dim):
            super().__init__()
            self.__initlayout(dim)
        def __initlayout(self, dim):
            self.grp1=QButtonGroup(self)
            self._btn1=[QRadioButton(str(d)) for d in range(dim)]
            layout = QHBoxLayout()
            layout.addWidget(QLabel("Axis"))
            for i, b in enumerate(self._btn1):
                self.grp1.addButton(b)
            for i, b in enumerate(self._btn1):
                layout.addWidget(b)
            layout.addStretch()
            self.setLayout(layout)
        def getAxis(self):
            return self._btn1.index(self.grp1.checkedButton())
    def __init__(self, executor):
        super().__init__()
        self.__initlayout()
        self.__exe=executor
    def __initlayout(self):
        self.layout = QVBoxLayout()

        self.__axis = self._axisWidget(2)

        btn = QPushButton("Create animation",clicked = self.__animation)
        self.__filename=QLineEdit()
        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel("Filename"))
        hbox1.addWidget(self.__filename)
        self.layout.addWidget(self.__axis)
        self.layout.addLayout(hbox1)
        self.layout.addLayout(self.__makeTimeOptionLayout())
        self.layout.addLayout(self.__makeScaleOptionLayout())
        self.layout.addStretch()
        self.layout.addWidget(btn)
        self.setLayout(self.layout)
    def __makeTimeOptionLayout(self):
        self.__useTime=QCheckBox('Draw time')
        self.__timeoffset=QDoubleSpinBox()
        self.__timeoffset.setRange(float('-inf'),float('inf'))
        self.__timeunit=QComboBox()
        self.__timeunit.addItems(['','ps','ns'])
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.__useTime)
        hbox1.addWidget(self.__timeoffset)
        hbox1.addWidget(self.__timeunit)
        return hbox1
    def __makeScaleOptionLayout(self):
        self.__usescale=QCheckBox('Draw scale')
        self.__scalesize=QDoubleSpinBox()
        self.__scalesize.setValue(1)
        self.__scalesize.setRange(0,float('inf'))
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.__usescale)
        hbox2.addWidget(self.__scalesize)
        return hbox2
    def _setWave(self,wave):
        self.wave=wave
        self.layout.removeWidget(self.__axis)
        self.__axis.deleteLater()
        self.__axis = self._axisWidget(wave.data.ndim)
        self.layout.insertWidget(0,self.__axis)
    def __loadCanvasSettings(self):
        import copy
        if Graph.active() is None:
            return None, None
        c=Graph.active().canvas
        dic={}
        for t in ['AxisSetting','TickSetting','AxisRange','LabelSetting','TickLabelSetting','Size','Margin']:
            dic[t]=c.SaveSetting(t)
        wd=c.getWaveData()
        return dic, wd
    def __animation(self):
        logging.info('[Animation] Analysis started.')
        dic, data = self.__loadCanvasSettings()
        if dic is None:
            logging.warning('[Animation] Prepare graph for reference.')
            return
        axis = self.wave.axes[self.__axis.getAxis()]
        self.__pexe = PointExecutor((self.__axis.getAxis(),))
        self.__exe.saveEnabledState()
        self.__exe.append(self.__pexe)
        params={}
        if self.__useTime.isChecked():
            params['time']={"unit":self.__timeunit.currentText(), "offset":self.__timeoffset.value()}
        if self.__usescale.isChecked():
            params['scale']={"size":self.__scalesize.value()}
        file = self.__filename.text()+".mp4"
        if file is None:
            file = "Animation.mp4"
        self._makeAnime(file, dic, data, axis, params, self.__pexe)
    def _makeAnime(self, file, dic, data, axis, params, exe):
        import copy
        c=ExtendCanvas()
        for key,value in dic.items():
            c.LoadSetting(key,value)
        for d in data:
            c.Append(d.wave, appearance = copy.deepcopy(d.appearance), offset = copy.deepcopy(d.offset))
        ani=animation.FuncAnimation(c.fig, _frame, fargs=(c, axis, params, exe), frames=len(axis), interval=30, repeat = False, init_func=_init)
        ani.save(file,writer='ffmpeg')
        self.__exe.remove(self.__pexe)
        self.__exe.restoreEnabledState()
        QMessageBox.information(None, "Info", "Animation is saved to "+file, QMessageBox.Yes)
        logging.info("Animation is saved to "+file)
        return file
def _init():
    pass
def _frame(i, c, axis, params, exe):
    exe.setPosition(axis[i])
    if "time" in params:
        _drawTime(c,axis[i],**params["time"])
def _drawTime(c,data=None,unit="",offset=0):
    c.clearAnnotations('text')
    t='{:.10g}'.format(round(data+float(offset),1))+" "+unit
    c.addText(t,x=0.1,y=0.1)
def _drawScale(c,size):
    xr=c.getAxisRange('Bottom')
    yr=c.getAxisRange('Left')
    x=xr[0]+(xr[1]-xr[0])*0.95
    y=yr[1]+(yr[0]-yr[1])*0.9
    id=c.addLine(([x-size,y],[x,y]))
    c.setAnnotLineColor('white',id)
_segtmp=None


def create():
    win=MultiCut()

addMainMenu(['Analysis','MultiCut'],create)
