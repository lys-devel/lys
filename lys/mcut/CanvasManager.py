import weakref

from lys import display, frontCanvas
from lys.Qt import QtWidgets, QtCore, QtGui
from lys.decorators import avoidCircularReference
from lys.widgets import lysCanvas, CanvasBase, Graph
from lys.widgets.canvas.interface import InfiniteLineAnnotation, RegionAnnotation, CrossAnnotation, RectAnnotation, FreeRegionAnnotation


class CanvasManager(list):
    def __init__(self, cui, color):
        super().__init__()
        self._cui = cui
        self._color = color
        self._wid = _InteractiveWidget(cui, self)
        self._sync = _AnnotationSync(cui, self)

    def createCanvas(self, axes, *args, graph=False, **kwargs):
        if graph:
            g = display(*args, **kwargs)
            g.setTitleColor(self._color)
            c = g.canvas
        else:
            c = lysCanvas(*args, **kwargs)
        c._maxes = axes
        self.append(c)
        c.finalized.connect(self.__removeCanvas)
        if self._wid is not None:
            c.clicked.connect(self._wid.setEnabled)
        return c

    def clear(self, removeGraphs=False):
        for w in self:
            self.__removeCanvas(w, removeGraphs)

    def __removeCanvas(self, canvas, removeGraphs=False):
        for an in canvas.getAnnotations():
            self._sync.unsyncAnnotation(an)
        if canvas in self:
            self.remove(canvas)
            parent = canvas.getParent()
            if isinstance(parent, Graph):
                if removeGraphs:
                    Graph.close(force=True)
                else:
                    parent.setTitleColor(QtGui.QColor())

    def _getTargetCanvas(self):
        c = frontCanvas()
        if c in self:
            return c
        else:
            if c is None:
                QtWidgets.QMessageBox.information(self._wid, "Error", "You should specify the canvas to add annoation.", QtWidgets.QMessageBox.Yes)
            else:
                QtWidgets.QMessageBox.information(self._wid, "Error", "You should specify the canvas that is created by MultiCut.", QtWidgets.QMessageBox.Yes)

    def addCross(self, c=None):
        if not isinstance(c, CanvasBase):
            c = self._getTargetCanvas()
        if c is not None:
            if self._sync.hasAnnotation(c, CrossAnnotation):
                QtWidgets.QMessageBox.information(self._wid, "Error", "This canvas already has same annotation.", QtWidgets.QMessageBox.Yes)
            else:
                crs = c.addCrossAnnotation()
                self._sync.syncAnnotation(crs)

    def addRect(self, c=None):
        if not isinstance(c, CanvasBase):
            c = self._getTargetCanvas()
        if c is not None:
            if self._sync.hasAnnotation(c, RectAnnotation):
                QtWidgets.QMessageBox.information(self._wid, "Error", "This canvas already has same annotation.", QtWidgets.QMessageBox.Yes)
            else:
                rect = c.addRectAnnotation()
                self._sync.syncAnnotation(rect)

    def addFreeLine(self, c=None, line=None, syncAnnot=False):
        if not isinstance(c, CanvasBase):
            c = self._getTargetCanvas()
        if c is not None:
            reg = c.addFreeRegionAnnotation()
            if line is None:
                line = self._cui.addFreeLine(c._maxes)
                self._sync.syncAnnotation(reg, line, syncAnnot=False)
            else:
                line = self._cui.getFreeLine(line)
                self._sync.syncAnnotation(reg, line, syncAnnot=syncAnnot)

    def addRegion(self, c=None, orientation="vertical"):
        if not isinstance(c, CanvasBase):
            c = self._getTargetCanvas()
        if c is not None:
            if self._sync.hasAnnotation(c, RegionAnnotation, orientation):
                QtWidgets.QMessageBox.information(self._wid, "Error", "This canvas already has same annotation.", QtWidgets.QMessageBox.Yes)
            else:
                reg = c.addRegionAnnotation(orientation=orientation)
                self._sync.syncAnnotation(reg)

    def addLine(self, c=None, orientation="vertical"):
        if not isinstance(c, CanvasBase):
            c = self._getTargetCanvas()
        if c is not None:
            if self._sync.hasAnnotation(c, InfiniteLineAnnotation, orientation):
                QtWidgets.QMessageBox.information(self._wid, "Error", "This canvas already has same annotation.", QtWidgets.QMessageBox.Yes)
            else:
                line = c.addInfiniteLineAnnotation(orientation=orientation)
                self._sync.syncAnnotation(line)

    def getAnnotations(self, c):
        res = []
        if self._sync.hasAnnotation(c, CrossAnnotation):
            res.append("cross")
        if self._sync.hasAnnotation(c, RectAnnotation):
            res.append("rect")
        if self._sync.hasAnnotation(c, RegionAnnotation, "vertical"):
            res.append("vertical_region")
        if self._sync.hasAnnotation(c, RegionAnnotation, "horizontal"):
            res.append("horizontal_region")
        if self._sync.hasAnnotation(c, InfiniteLineAnnotation, "vertical"):
            res.append("vertical_line")
        if self._sync.hasAnnotation(c, InfiniteLineAnnotation, "horizontal"):
            res.append("horizontal_line")
        res.extend(self._sync.lineAnnotations(c))
        return res

    def addAnnotations(self, c, annotations, syncLine=False):
        for annot in annotations:
            if annot == "cross":
                self.addCross(c)
            elif annot == "rect":
                self.addRect(c)
            elif annot == "vertical_region":
                self.addRegion(c, orientation="vertical")
            elif annot == "horizontal_region":
                self.addRegion(c, orientation="horizontal")
            elif annot == "vertical_line":
                self.addLine(c, orientation="vertical")
            elif annot == "horizontal_line":
                self.addLine(c, orientation="horizontal")
            else:
                self.addFreeLine(c, annot, syncLine)

    def interactiveWidget(self):
        return self._wid


class _AnnotationSync(QtCore.QObject):
    def __init__(self, cui, can):
        super().__init__()
        self._sync = {}
        self._cui = cui
        self._can = weakref.ref(can)

    def syncAnnotation(self, annot, line=None, syncAnnot=False):
        c = annot.canvas()
        if c not in self._can():
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
            self._sync[annot] = _FreeLineSync(self._cui, annot, line, syncAnnot=syncAnnot)

    def unsyncAnnotation(self, annot):
        if annot in self._sync:
            del self._sync[annot]

    def hasAnnotation(self, canvas, type, orientation=None):
        for annot in self._sync.keys():
            if annot.canvas() == canvas and isinstance(annot, type):
                if orientation is None:
                    return True
                elif annot.getOrientation() == orientation:
                    return True
        return False

    def lineAnnotations(self, canvas):
        res = []
        for annot in self._sync.keys():
            if annot.canvas() == canvas and isinstance(annot, FreeRegionAnnotation):
                res.append(self._sync[annot].getName())
        return res


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
        if self._cui.getAxisRangeType(self._axis) == "point":
            self._annot.setPosition(self._cui.getAxisRange(self._axis))
        else:
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
        pos = []
        for i, ax in enumerate(self._axes):
            if self._cui.getAxisRangeType(ax) == "point":
                pos.append(self._cui.getAxisRange(ax))
            else:
                pos.append(self._annot.getPosition()[i])
        self._annot.setPosition(pos)
        self._cui.setAxisRange(self._axes, pos)
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
        if self._cui.getAxisRangeType(self._axis) == "range":
            self._annot.setRegion(self._cui.getAxisRange(self._axis))
        else:
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
        r = []
        for i, ax in enumerate(self._axes):
            if self._cui.getAxisRangeType(ax) == "range":
                r.append(self._cui.getAxisRange(ax))
            else:
                r.append(self._annot.getRegion()[i])
        self._annot.setRegion(r)
        self._cui.setAxisRange(self._axes, r)
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
    def __init__(self, cui, annot, line, syncAnnot):
        super().__init__()
        self._annot = annot
        self._cui = cui
        self._line = line
        self._sync(syncAnnot)

    def getName(self):
        return self._line.getName()

    def _sync(self, syncAnnot):
        if syncAnnot:
            self._annot.setRegion(self._line.getPosition())
            self._annot.setWidth(self._line.getWidth())
        else:
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


class _InteractiveWidget(QtWidgets.QGroupBox):
    def __init__(self, cui, canvases):
        super().__init__("Interactive Annotations")
        self._cui = cui
        self._can = weakref.ref(canvases)
        self.__initlayout()

    def __initlayout(self):
        self._lx = QtWidgets.QPushButton("Line (X)", clicked=self.__addLineX)
        self._ly = QtWidgets.QPushButton("Line (Y)", clicked=self.__addLineY)
        self._rx = QtWidgets.QPushButton("Region (X)", clicked=self.__addRegionX)
        self._ry = QtWidgets.QPushButton("Region (Y)", clicked=self.__addRegionY)
        self._pt = QtWidgets.QPushButton("Point", clicked=self.__addPoint)
        self._rt = QtWidgets.QPushButton("Rect", clicked=self.__addRect)
        self._li = QtWidgets.QPushButton("Free Line", clicked=self.__addFreeLine)
        for w in [self._lx, self._ly, self._rx, self._ry, self._pt, self._rt, self._li]:
            w.setEnabled(False)

        mc = QtWidgets.QComboBox()
        mc.addItems(["Mean", "Sum", "Median", "Max", "Min"])
        mc.currentTextChanged.connect(self._cui.setSumType)

        grid = QtWidgets.QGridLayout()
        grid.addWidget(self._lx, 0, 0)
        grid.addWidget(self._ly, 0, 1)
        grid.addWidget(self._rx, 1, 0)
        grid.addWidget(self._ry, 1, 1)
        grid.addWidget(self._pt, 2, 0)
        grid.addWidget(self._rt, 2, 1)
        grid.addWidget(self._li, 3, 0)
        grid.addWidget(mc, 3, 1)

        self.setLayout(grid)

    def __addLineX(self):
        self._can().addLine(orientation="vertical")

    def __addLineY(self):
        self._can().addLine(orientation="horizontal")

    def __addRegionX(self):
        self._can().addRegion(orientation="vertical")

    def __addRegionY(self):
        self._can().addRegion(orientation="horizontal")

    def __addPoint(self):
        self._can().addCross()

    def __addRect(self):
        self._can().addRect()

    def __addFreeLine(self):
        self._can().addFreeLine()

    def setEnabled(self):
        c = frontCanvas()
        if len(c._maxes) == 1:
            if isinstance(c._maxes[0], str):
                for w in [self._lx, self._ly, self._rx, self._ry, self._pt, self._rt, self._li]:
                    w.setEnabled(False)
            else:
                for w in [self._lx, self._rx]:
                    w.setEnabled(True)
                for w in [self._ly, self._ry, self._pt, self._rt, self._li]:
                    w.setEnabled(False)
        else:
            for w in [self._lx, self._ly, self._rx, self._ry, self._pt, self._rt, self._li]:
                w.setEnabled(True)
            if isinstance(c._maxes[0], str):
                for w in [self._lx, self._rx, self._pt, self._rt, self._li]:
                    w.setEnabled(False)
            if isinstance(c._maxes[1], str):
                for w in [self._ly, self._ry, self._pt, self._rt, self._li]:
                    w.setEnabled(False)
