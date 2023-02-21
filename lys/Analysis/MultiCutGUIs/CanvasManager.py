
from lys import display, frontCanvas
from lys.Qt import QtWidgets, QtCore
from lys.decorators import avoidCircularReference
from lys.widgets import lysCanvas, CanvasBase
from lys.widgets.canvas.interface import InfiniteLineAnnotation, RegionAnnotation, CrossAnnotation, RectAnnotation, FreeRegionAnnotation


class CanvasManager(list):
    def __init__(self, cui):
        super().__init__()
        self._index = 0
        self._cui = cui
        self._sync = {}

    def createCanvas(self, axes, *args, graph=False, **kwargs):
        if graph:
            c = display(*args, **kwargs).canvas
        else:
            c = lysCanvas(*args, **kwargs)
        c._maxes = axes
        self._index = self._index + 1
        c._mname = "canvas" + str(self._index)
        self.append(c)
        c.finalized.connect(self.__removeCanvas)
        return c

    def __removeCanvas(self, canvas):
        for an in canvas.getAnnotations():
            self.unsyncAnnotation(an)
        self.remove(canvas)

    def syncAnnotation(self, annot, line=None):
        c = annot.canvas()
        if c not in self:
            raise RuntimeWarning("Could not synchronize annotations in canvas that is not controlled by CanvasManager.")
        if annot in self._sync:
            return
        if isinstance(annot, InfiniteLineAnnotation):
            self._sync[annot] = _InfLineSync(self._cui, annot)
        if isinstance(annot, RegionAnnotation):
            self._sync[annot] = _RegionSync(self._cui, annot)
        if isinstance(annot, CrossAnnotation):
            self._sync[annot] = _CrossSync(self._cui, annot)
        if isinstance(annot, RectAnnotation):
            self._sync[annot] = _RectSync(self._cui, annot)
        if isinstance(annot, FreeRegionAnnotation) and line is not None:
            self._sync[annot] = _FreeLineSync(self._cui, annot, line)

    def unsyncAnnotation(self, annot):
        if annot in self._sync:
            del self._sync[annot]

    def widget(self):
        return _InteractiveWidget(self._cui, self)


class _InfLineSync(QtCore.QObject):
    def __init__(self, cui, annot):
        super().__init__()
        self._annot = annot
        self._cui = cui
        self._sync()

    def _sync(self):
        c = self._annot.canvas()
        if self._annot.getOrientation() == "vertical":
            self._axis = c._maxes[0]
        else:
            self._axis = c._maxes[1]
        self._cui.setAxisRange(self._axis, self._annot.getPosition())
        self._annot.positionChanged.connect(self.__sync)
        self._cui.axesRangeChanged.connect(self.__sync_r)

    @avoidCircularReference
    def __sync(self, value):
        if self._cui.getAxisRangeType(self._axis) == 'point':
            self._cui.setAxisRange(self._axis, value)

    @avoidCircularReference
    def __sync_r(self, axes):
        if self._axis in axes and self._cui.getAxisRangeType(self._axis) == 'point':
            self._annot.setPosition(self._cui.getAxisRange(self._axis))


class _CrossSync(QtCore.QObject):
    def __init__(self, cui, annot):
        super().__init__()
        self._annot = annot
        self._cui = cui
        self._sync()

    def _sync(self):
        c = self._annot.canvas()
        self._axes = c._maxes
        self._cui.setAxisRange(self._axes, self._annot.getPosition())
        self._annot.positionChanged.connect(self.__sync)
        self._cui.axesRangeChanged.connect(self.__sync_r)

    @avoidCircularReference
    def __sync(self, value):
        for i, ax in enumerate(self._axes):
            if self._cui.getAxisRangeType(ax) == 'point':
                self._cui.setAxisRange(ax, value[i])

    @avoidCircularReference
    def __sync_r(self, axes):
        if self._axes[0] not in axes and self._axes[1] not in axes:
            return
        pos = list(self._annot.getPosition())
        for i, ax in enumerate(self._axes):
            if ax in axes and self._cui.getAxisRangeType(ax) == 'point':
                pos[i] = self._cui.getAxisRange(ax)
        self._annot.setPosition(pos)


class _RegionSync(QtCore.QObject):
    def __init__(self, cui, annot):
        super().__init__()
        self._annot = annot
        self._cui = cui
        self._sync()

    def _sync(self):
        c = self._annot.canvas()
        if self._annot.getOrientation() == "vertical":
            self._axis = c._maxes[0]
        else:
            self._axis = c._maxes[1]
        self._cui.setAxisRange(self._axis, self._annot.getRegion())
        self._annot.regionChanged.connect(self.__sync)
        self._cui.axesRangeChanged.connect(self.__sync_r)

    @avoidCircularReference
    def __sync(self, value):
        if self._cui.getAxisRangeType(self._axis) == 'range':
            self._cui.setAxisRange(self._axis, value)

    @avoidCircularReference
    def __sync_r(self, axes):
        if self._axis in axes and self._cui.getAxisRangeType(self._axis) == 'range':
            self._annot.setRegion(self._cui.getAxisRange(self._axis))


class _RectSync(QtCore.QObject):
    def __init__(self, cui, annot):
        super().__init__()
        self._annot = annot
        self._cui = cui
        self._sync()

    def _sync(self):
        c = self._annot.canvas()
        self._axes = c._maxes
        self._cui.setAxisRange(self._axes, self._annot.getRegion())
        self._annot.regionChanged.connect(self.__sync)
        self._cui.axesRangeChanged.connect(self.__sync_r)

    @avoidCircularReference
    def __sync(self, value):
        for i, ax in enumerate(self._axes):
            if self._cui.getAxisRangeType(ax) == 'range':
                self._cui.setAxisRange(ax, value[i])

    @avoidCircularReference
    def __sync_r(self, axes):
        if self._axes[0] not in axes and self._axes[1] not in axes:
            return
        r = self._annot.getRegion()
        for i, ax in enumerate(self._axes):
            if ax in axes and self._cui.getAxisRangeType(ax) == 'range':
                r[i] = self._cui.getAxisRange(ax)
        self._annot.setRegion(r)


class _FreeLineSync(QtCore.QObject):
    def __init__(self, cui, annot, line):
        super().__init__()
        self._annot = annot
        self._cui = cui
        self._line = line
        self._sync()

    def _sync(self):
        self._line.setPosition(self._annot.getRegion())
        self._line.setWidth(self._annot.getWidth())
        self._annot.regionChanged.connect(self.__sync_p)
        self._annot.widthChanged.connect(self.__sync_w)
        self._line.lineChanged.connect(self.__sync_r)

    @avoidCircularReference
    def __sync_p(self, value):
        self._line.setPosition(value)

    @avoidCircularReference
    def __sync_w(self, value):
        self._line.setWidth(value)

    @avoidCircularReference
    def __sync_r(self):
        self._annot.setRegion(self._line.getPosition())
        self._annot.setWidth(self._line.getWidth())


class _CanvasList(QtWidgets.QTreeView):
    def __init__(self, obj):
        super().__init__()
        self._model = _CanvasListModel(obj)
        self.setModel(self._model)


class _CanvasListModel(QtCore.QAbstractItemModel):
    def __init__(self, obj):
        super().__init__()
        self.obj = obj

    def _annotations(self, canvas):
        res = []
        res.extend(canvas.getInfiniteLineAnnotations())
        res.extend(canvas.getRegionAnnotations())
        res.extend(canvas.getCrossAnnotations())
        res.extend(canvas.getRectAnnotations())
        res.extend(canvas.getFreeRegionAnnotations())
        return res

    def data(self, index, role):
        if not index.isValid() or not role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        c = index.internalPointer()
        if isinstance(c, CanvasBase):
            if index.column() == 0:
                return c._mname
            elif index.column() == 1:
                return str(tuple(c._maxes))
        else:
            if index.column() == 0:
                return c.getName()
            else:
                return "test"

    def rowCount(self, parent):
        if not parent.isValid():  # top level
            return len(self.obj)
        elif isinstance(parent.internalPointer(), CanvasBase):  # canvas
            return len(self._annotations(parent.internalPointer()))
        else:  # annotations
            return 0

    def columnCount(self, parent):
        return 2

    def index(self, row, column, parent):
        if not parent.isValid():
            if len(self.obj) > row:
                return self.createIndex(row, column, self.obj[row])
        elif isinstance(parent.internalPointer(), CanvasBase):
            return self.createIndex(row, column, self._annotations(parent.internalPointer())[row])
        return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        elif isinstance(index.internalPointer(), CanvasBase):
            return QtCore.QModelIndex()
        else:
            c = index.internalPointer().canvas()
            return self.createIndex(self.obj.index(c), 0, c)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section == 0:
                return "Name"
            else:
                return "Axes"


class _InteractiveWidget(QtWidgets.QGroupBox):
    def __init__(self, cui, canvases):
        super().__init__("Interactive")
        self._cui = cui
        self._can = canvases
        self.__initlayout()

    def __initlayout(self):
        lx = QtWidgets.QPushButton("Line (X)", clicked=self._linex)
        ly = QtWidgets.QPushButton("Line (Y)", clicked=self._liney)
        rx = QtWidgets.QPushButton("Region (X)", clicked=self._regx)
        ry = QtWidgets.QPushButton("Region (Y)", clicked=self._regy)
        pt = QtWidgets.QPushButton("Point", clicked=self._point)
        rt = QtWidgets.QPushButton("Rect", clicked=self._rect)
        li = QtWidgets.QPushButton("Free Line", clicked=self._line)

        mc = QtWidgets.QComboBox()
        mc.addItems(["Mean", "Sum", "Median", "Max", "Min"])
        mc.currentTextChanged.connect(self._cui.setSumType)

        grid = QtWidgets.QGridLayout()
        grid.addWidget(lx, 0, 0)
        grid.addWidget(ly, 0, 1)
        grid.addWidget(rx, 1, 0)
        grid.addWidget(ry, 1, 1)
        grid.addWidget(pt, 2, 0)
        grid.addWidget(rt, 2, 1)
        grid.addWidget(li, 3, 0)
        grid.addWidget(mc, 3, 1)

        #self._tree = QtWidgets.QTreeView()
        # self._tree.setModel(_CanvasListModel(self._can))

        hbox = QtWidgets.QHBoxLayout()
        hbox.addLayout(grid)
        # hbox.addWidget(self._tree)
        self.setLayout(hbox)

    def _getTargetCanvas(self):
        c = frontCanvas()
        if c in self._can:
            return c

    def _point(self, c=None):
        if not isinstance(c, CanvasBase):
            c = self._getTargetCanvas()
        crs = c.addCrossAnnotation()
        self._can.syncAnnotation(crs)

    def _rect(self, c=None):
        if not isinstance(c, CanvasBase):
            c = self._getTargetCanvas()
        rect = c.addRectAnnotation()
        self._can.syncAnnotation(rect)

    def _line(self, c=None):
        if not isinstance(c, CanvasBase):
            c = self._getTargetCanvas()
        reg = c.addFreeRegionAnnotation()
        line = self._cui.addFreeLine(c._maxes)
        self._can.syncAnnotation(reg, line)

    def _regx(self, c=None):
        if not isinstance(c, CanvasBase):
            c = self._getTargetCanvas()
        reg = c.addRegionAnnotation()
        self._can.syncAnnotation(reg)

    def _regy(self, c=None):
        if not isinstance(c, CanvasBase):
            c = self._getTargetCanvas()
        reg = c.addRegionAnnotation(orientation="horizontal")
        self._can.syncAnnotation(reg)

    def _linex(self, c=None):
        if not isinstance(c, CanvasBase):
            c = self._getTargetCanvas()
        line = c.addInfiniteLineAnnotation()
        self._can.syncAnnotation(line)

    def _liney(self, c=None):
        if not isinstance(c, CanvasBase):
            c = self._getTargetCanvas()
        line = c.addInfiniteLineAnnotation(orientation='horizontal')
        self._can.syncAnnotation(line)
