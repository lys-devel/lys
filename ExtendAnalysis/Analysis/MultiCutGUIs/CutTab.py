from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from ..MultiCut import *
from ExtendAnalysis import MainWindow


class ControlledObjectsModel(QAbstractItemModel):
    def __init__(self, obj):
        super().__init__()
        self.obj = obj
        obj.appended.connect(lambda x: self.layoutChanged.emit())
        obj.removed.connect(lambda x: self.layoutChanged.emit())
        self.setHeaderData(0, Qt.Horizontal, 'Name')
        self.setHeaderData(1, Qt.Horizontal, 'Axes')

    def data(self, index, role):
        if not index.isValid() or not role == Qt.DisplayRole:
            return QVariant()
        item = index.internalPointer()
        if item is not None:
            if index.column() == 0:
                return item.Name()
            elif index.column() == 1:
                return str(item)

    def rowCount(self, parent):
        if parent.isValid():
            return 0
        return len(self.obj)

    def columnCount(self, parent):
        return 2

    def index(self, row, column, parent):
        if not parent.isValid():
            return self.createIndex(row, column, self.obj[row][column])
        return QModelIndex()

    def parent(self, index):
        return QModelIndex()

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return "Name"
            else:
                return "Axes"


class SwitchableModel(ControlledObjectsModel):
    def data(self, index, role):
        item = index.internalPointer()
        if item is not None and role == Qt.ForegroundRole:
            if self.obj.isEnabled(index.row()):
                return QBrush(QColor("black"))
            else:
                return QBrush(QColor("gray"))
        return super().data(index, role)


class controlledWavesGUI(QTreeView):
    updated = pyqtSignal()

    def __init__(self, obj, dispfunc, appendfunc, parent=None):
        super().__init__(parent)
        self.obj = obj
        self.disp = dispfunc
        self.apnd = appendfunc
        self.__model = SwitchableModel(obj)
        self.setModel(self.__model)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)

    def buildContextMenu(self):
        menu = QMenu(self)
        menu.addAction(QAction("Display", self, triggered=self._display))
        menu.addAction(QAction("Append", self, triggered=self._append))
        menu.addAction(
            QAction("Append Contour", self, triggered=self._contour))
        menu.addAction(QAction("Enable", self, triggered=self._enable))
        menu.addAction(QAction("Disable", self, triggered=self._disable))
        menu.addAction(QAction("Remove", self, triggered=self._remove))
        menu.addAction(QAction("PostProcess", self, triggered=self._post))
        menu.exec_(QCursor.pos())

    def _display(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.disp(*self.obj[i])

    def _append(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.apnd(*self.obj[i])

    def _contour(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.apnd(*self.obj[i], contour=True)

    def _remove(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.obj.removeAt(i)

    def _post(self):
        class dialog(FiltersDialog):
            def __init__(self, wave):
                super().__init__(wave.data.ndim)
                self.wave = wave
                self.applied.connect(self.__set)

            def __set(self, f):
                w.note['MultiCut_PostProcess'] = str(f)
        i = self.selectionModel().selectedIndexes()[0].row()
        w = self.obj[i][0]
        self.d = d = dialog(w)
        d.applied.connect(self.updated.emit)
        if 'MultiCut_PostProcess' in w.note:
            d.setFilter(Filters.fromString(w.note['MultiCut_PostProcess']))
        d.show()

    def _enable(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.obj.enableAt(i)

    def _disable(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.obj.disableAt(i)

    def sizeHint(self):
        return QSize(100, 100)


class controlledExecutorsGUI(QTreeView):
    def __init__(self, obj, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.obj = obj
        self.__model = SwitchableModel(obj)
        self.setModel(self.__model)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)

    def buildContextMenu(self):
        menu = QMenu(self)
        menu.addAction(QAction("Setting", self, triggered=self._setting))
        menu.addAction(QAction("Enable", self, triggered=self._enable))
        menu.addAction(QAction("Disable", self, triggered=self._disable))
        menu.addAction(QAction("Remove", self, triggered=self._remove))
        menu.exec_(QCursor.pos())

    def _setting(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.obj.setting(i, parentWidget=self.parent.parent.parent)

    def _remove(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.obj.removeAt(i)

    def _enable(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.obj.enableAt(i)

    def _disable(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        self.obj.disableAt(i)

    def sizeHint(self):
        return QSize(100, 100)


class _axisLayout(QWidget):
    def __init__(self, dim):
        super().__init__()
        self.__initlayout(dim)
        self._lineids = {}

    def __initlayout(self, dim):
        self.grp1 = QButtonGroup(self)
        self.grp2 = QButtonGroup(self)
        self._btn1 = [QRadioButton(str(d)) for d in range(dim)]
        self._btn2 = [QRadioButton(str(d)) for d in range(dim)]
        self._btn2.insert(0, QRadioButton("None"))
        self._btn1.append(QRadioButton("Line"))
        self._btn2.append(QRadioButton("Line"))
        self._cmb1 = QComboBox()
        self._cmb2 = QComboBox()
        layout = QGridLayout()
        layout.addWidget(QLabel("1st Axis"), 0, 0)
        layout.addWidget(QLabel("2nd Axis"), 1, 0)
        for i, b in enumerate(self._btn1):
            self.grp1.addButton(b)
        for i, b in enumerate(self._btn1):
            layout.addWidget(b, 0, i + 2)
        layout.addWidget(self._cmb1, 0, len(self._btn1) + 2)
        for i, b in enumerate(self._btn2):
            self.grp2.addButton(b)
        for i, b in enumerate(self._btn2):
            layout.addWidget(b, 1, i + 1)
        layout.addWidget(self._cmb2, 1, len(self._btn2) + 1)
        self.setLayout(layout)

    def updateLines(self, lines):
        for c in [self._cmb1, self._cmb2]:
            old = c.currentText()
            for i in range(c.count()):
                c.removeItem(0)
            for i, l in enumerate(lines):
                c.addItem(l.Name())
                if l.Name() == old:
                    c.setCurrentIndex(i)
        self._lineids = {}
        for l in lines:
            self._lineids[l.Name()] = l.ID()

    def getAxes(self):
        ax1 = self._btn1.index(self.grp1.checkedButton())
        ax2 = self._btn2.index(self.grp2.checkedButton()) - 1
        if ax1 == len(self._btn1) - 1:
            ax1 = self._lineids[self._cmb1.currentText()]
        if ax2 == len(self._btn2) - 2:
            ax2 = self._lineids[self._cmb2.currentText()]
        if ax2 == -1:
            return (ax1,)
        else:
            return (ax1, ax2)


class _gridTableWidget(QTableWidget):
    def __init__(self, size, parent=None):
        super().__init__(parent)
        self.size = size
        self.setRowCount(size)
        self.setColumnCount(size)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._tableContext)

    def _tableContext(self, pos):
        menu = QMenu(self)
        togrid = menu.addAction("Graph -> Grid (Not implemented)")
        tograph = menu.addAction("Grid -> Graph (Not implemented)")
        intergrid = menu.addAction("Grid -> Grid (Not implemented)")
        menu.exec_(self.mapToGlobal(pos))

    def getGridPos(self):
        rows = [i.row() for i in self.selectionModel().selectedIndexes()]
        columns = [i.column() for i in self.selectionModel().selectedIndexes()]
        if len(rows) * len(columns) == 0:
            return (0, 0), (self.size, self.size)
        return (np.min(rows), np.min(columns)), (np.max(rows) - np.min(rows) + 1, np.max(columns) - np.min(columns) + 1)


class _InteractiveWidget(QGroupBox):
    def __init__(self, exe, canvases, parent):
        super().__init__("Interactive")
        self.parent = parent
        self.__exe = exe
        self.canvases = canvases
        self.__cut = parent
        self.__initlayout()

    def __initlayout(self):
        lx = QPushButton("Line (X)", clicked=self._linex)
        ly = QPushButton("Line (Y)", clicked=self._liney)
        rx = QPushButton("Region (X)", clicked=self._regx)
        ry = QPushButton("Region (Y)", clicked=self._regy)
        pt = QPushButton("Point", clicked=self._point)
        rt = QPushButton("Rect", clicked=self._rect)
        cc = QPushButton("Circle", clicked=self._circle)
        li = QPushButton("Free Line", clicked=self._line)

        mc = QComboBox()
        mc.addItems(["Sum", "Mean", "Median", "Max", "Min"])
        mc.currentTextChanged.connect(lambda t: self.__exe.setSumType(t))

        grid = QGridLayout()
        grid.addWidget(lx, 0, 0)
        grid.addWidget(ly, 0, 1)
        grid.addWidget(rx, 1, 0)
        grid.addWidget(ry, 1, 1)
        grid.addWidget(pt, 2, 0)
        grid.addWidget(rt, 2, 1)
        grid.addWidget(cc, 3, 0)
        grid.addWidget(li, 3, 1)
        grid.addWidget(mc, 4, 0)

        elist = controlledExecutorsGUI(self.__exe, self)
        hbox = QHBoxLayout()
        hbox.addLayout(grid)
        hbox.addWidget(elist)
        self.setLayout(hbox)

    def _getTargetCanvas(self):
        return self.__cut.getTargetCanvas()

    def _point(self, c=None):
        if not isinstance(c, CanvasBaseBase):
            c = self._getTargetCanvas()
        id = c.addCross()
        e = PointExecutor(self.canvases.getAxes(c))
        c.addCallback(id, e.callback)
        e.updated.connect(lambda x: c.setCrosshairPosition(c.getAnnotations(indexes=id)[0], e.getPosition()))
        self.__exe.append(e, c)

    def _rect(self, c=None):
        if not isinstance(c, CanvasBaseBase):
            c = self._getTargetCanvas()
        id = c.addRect()
        e = RegionExecutor(self.canvases.getAxes(c))
        c.addCallback(id, e.callback)
        e.updated.connect(lambda x: c.setRectRegion(c.getAnnotations(indexes=id)[0], e.getRange()))
        self.__exe.append(e, c)

    def _circle(self):
        pass

    def _line(self, c=None):
        if not isinstance(c, CanvasBaseBase):
            c = self._getTargetCanvas()
        id = c.addLine()
        e = FreeLineExecutor(self.canvases.getAxes(c))
        c.addCallback(id, e.callback)
        e.updated.connect(lambda x: c.setAnnotLinePosition(c.getAnnotations(indexes=id)[0], e.getPosition()))
        self.__exe.append(e, c)

    def _regx(self, c=None):
        if not isinstance(c, CanvasBaseBase):
            c = self._getTargetCanvas()
        id = c.addRegion()
        e = RegionExecutor(self.canvases.getAxes(c)[0])
        c.addCallback(id, e.callback)
        e.updated.connect(lambda x: c.setRegion(c.getAnnotations(indexes=id)[0], e.getRange()[0]))
        self.__exe.append(e, c)

    def _regy(self, c=None):
        if not isinstance(c, CanvasBaseBase):
            c = self._getTargetCanvas()
        id = c.addRegion(type="horizontal")
        e = RegionExecutor(self.canvases.getAxes(c)[1])
        c.addCallback(id, e.callback)
        e.updated.connect(lambda x: c.setRegion(c.getAnnotations(indexes=id)[0], e.getRange()[0]))
        self.__exe.append(e, c)

    def _linex(self, c=None):
        if not isinstance(c, CanvasBaseBase):
            c = self._getTargetCanvas()
        id = c.addInfiniteLine()
        e = PointExecutor(self.canvases.getAxes(c)[0])
        c.addCallback(id, e.callback)
        e.updated.connect(lambda x: c.setInfiniteLinePosition(c.getAnnotations(indexes=id)[0], e.getPosition()[0]))
        self.__exe.append(e, c)

    def _liney(self, c=None):
        if not isinstance(c, CanvasBaseBase):
            c = self._getTargetCanvas()
        id = c.addInfiniteLine(type='horizontal')
        e = PointExecutor(self.canvases.getAxes(c)[1])
        c.addCallback(id, e.callback)
        e.updated.connect(lambda x: c.setInfiniteLinePosition(c.getAnnotations(indexes=id)[0], e.getPosition()[0]))
        self.__exe.append(e, c)


class CutTab(QWidget):
    def __init__(self, parent, grid):
        super().__init__()
        self.parent = parent
        self.grid = grid
        self.grid.setSize(4)

        self.__exe = ExecutorList()
        self.__exe.updated.connect(self.update)
        self.__exe.appended.connect(lambda: self.ax.updateLines(self.__exe.getFreeLines()))
        self.__exe.removed.connect(lambda: self.ax.updateLines(self.__exe.getFreeLines()))

        self.waves = SwitchableObjects()
        self.canvases = controlledObjects()
        self.canvases.removed.connect(self.__exe.graphRemoved)
        self.__initlayout__()
        self.ax = None
        self.wave = None

    def __initlayout__(self):
        self.wlist = controlledWavesGUI(self.waves, self.display, self.append)
        self.wlist.updated.connect(self.update)

        self._table = _gridTableWidget(4)
        self._usegraph = QCheckBox("Use Graph")
        v1 = QVBoxLayout()
        v1.addWidget(self._usegraph)
        v1.addWidget(self._table)

        h1 = QHBoxLayout()
        h1.addWidget(self.wlist, 2)
        h1.addLayout(v1, 1)

        disp = QPushButton("Display", clicked=self.display)
        make = QPushButton("Make", clicked=self.make)
        typ = QPushButton("Typical", clicked=self.typical)
        hbox = QHBoxLayout()
        hbox.addWidget(make)
        hbox.addWidget(disp)
        hbox.addWidget(typ)

        self._make = QVBoxLayout()
        self._make.addLayout(h1)
        self._make.addLayout(hbox)

        make = QGroupBox("Waves")
        make.setLayout(self._make)

        grp = _InteractiveWidget(self.__exe, self.canvases, self)

        self.layout = QVBoxLayout()
        self.layout.addWidget(make, 1)
        self.layout.addWidget(grp, 1)
        self.layout.addStretch()

        self.setLayout(self.layout)

    def _setWave(self, wave):
        old = self.wave
        self.wave = wave
        if old is None:
            self.__resetLayout()
            return
        if old.data.shape != wave.data.shape:
            self.__resetLayout()
            return
        self.update()

    def __resetLayout(self):
        if self.ax is not None:
            self._make.removeWidget(self.ax)
            self.ax.deleteLater()
        self.ax = _axisLayout(self.wave.data.ndim)
        self._make.insertWidget(1, self.ax)
        self.waves.clear()
        self.canvases.clear()
        self.__exe.clear()
        self.adjustSize()

    def make(self, axes=None):
        if not hasattr(axes, "__iter__"):
            if self.ax is None:
                return
            ax = self.ax.getAxes()
        else:
            ax = axes
        if len(ax) in [1, 2]:
            w = self.__exe.makeWave(self.wave, ax)
            self.waves.append(w, ax)
            return w
        else:
            return None

    def display(self, wave=None, axes=None, pos=None, wid=None):
        if not hasattr(axes, "__iter__"):
            ax = self.ax.getAxes()
        else:
            ax = axes
        if not isinstance(wave, Wave):
            w = self.make(ax)
        else:
            w = wave
        if w is not None:
            if self._usegraph.isChecked():
                g = display(w, lib="pyqtgraph")
                self.canvases.append(g.canvas, ax)
                g.canvas.deleted.connect(self.canvases.remove)
                g.canvas.clicked.connect(lambda x, y: self._gridClicked(g.canvas))
                return g.canvas
            else:
                if self.getTargetCanvas() is not None:
                    msgBox = QMessageBox()
                    msgBox.setText("There is a graph at this position. Do you really want to proceed?")
                    yes = msgBox.addButton(QMessageBox.Yes)
                    graph = msgBox.addButton("Use Graph", QMessageBox.ActionRole)
                    no = msgBox.addButton(QMessageBox.No)
                    msgBox.exec_()
                    if msgBox.clickedButton() == no:
                        return
                    elif msgBox.clickedButton() == graph:
                        self._usegraph.setChecked(True)
                        return self.display(wave, axes, pos, wid)
                if pos == None or wid == None:
                    pos, wid = self._table.getGridPos()
                c = pyqtCanvas()
                c.Append(w)
                c.keyPressed.connect(self.parent.keyPress)
                self.canvases.append(c, ax)
                c.deleted.connect(self.canvases.remove)
                c.clicked.connect(lambda x, y: self._gridClicked(c))
                self.grid.Append(c, *pos, *wid)
                return c

    def _gridClicked(self, canvas):
        b = False
        for i in range(4):
            for j in range(4):
                if self.grid.itemAtPosition(i, j) == canvas:
                    self._table.setCurrentCell(i, j, QItemSelectionModel.Select)
                    b = True
                else:
                    self._table.setCurrentCell(i, j, QItemSelectionModel.Deselect)
        self._usegraph.setChecked(not b)

    def append(self, wave, axes, contour=False):
        c = self.getTargetCanvas()
        c.Append(wave, contour=contour)

    def getTargetCanvas(self):
        if self._usegraph.isChecked():
            return Graph.active().canvas
        else:
            pos, wid = self._table.getGridPos()
            return self.grid.itemAtPosition(*pos)

    def update(self, index=None):
        for w, axs in self.waves.getObjectsAndAxes():
            if index is None:
                self.__updateSingleWave(w, axs)
                continue
            elif index[0] < 10000:
                if not set(index).issubset(axs):
                    self.__updateSingleWave(w, axs)
            else:
                if index[0] in axs:
                    self.__updateSingleWave(w, axs)

    def __updateSingleWave(self, w, axs):
        if not self.waves.isEnabled(w):
            return
        try:
            wav = self.__exe.makeWave(self.wave, axs)
            w.axes = wav.axes
            w.data = wav.data
            if "MultiCut_PostProcess" in w.note:
                filt = Filters.fromString(w.note["MultiCut_PostProcess"])
                filt.execute(w)
        except:
            import traceback
            traceback.print_exc()

    def typical(self):
        if self.wave.data.ndim == 2:
            self.typical2d()
        if self.wave.data.ndim == 3:
            self.typical3d()
        if self.wave.data.ndim == 4:
            self.typical4d()
        if self.wave.data.ndim == 5:
            self.typical5d()

    def typical2d(self):
        c1 = self.display(axes=[0, 1], pos=[0, 0], wid=[4, 4])

    def typical3d(self):
        c1 = self.display(axes=[2], pos=[3, 0], wid=[1, 4])
        c2 = self.display(axes=[0, 1], pos=[0, 0], wid=[3, 4])
        self._linex(c1)
        self._rect(c2)

    def typical4d(self):
        c1 = self.display(axes=[0, 1], pos=[0, 0], wid=[4, 2])
        c2 = self.display(axes=[2, 3], pos=[0, 2], wid=[4, 2])
        self._rect(c1)
        self._rect(c2)

    def typical5d(self):
        c1 = self.display(axes=[0, 1], pos=[0, 0], wid=[3, 2])
        c2 = self.display(axes=[2, 3], pos=[0, 2], wid=[3, 2])
        c3 = self.display(axes=(4,), pos=[3, 0], wid=[1, 4])
        self._rect(c1)
        self._rect(c2)
        self._linex(c3)

    def getExecutorList(self):
        return self.__exe

    def findAxisFromCanvas(self, canvas):
        return self.canvases.getAxes(canvas)
