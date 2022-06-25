import warnings
import numpy as np
import pyqtgraph as pg

from lys.Qt import QtCore, QtGui
from lys.errors import NotSupportedWarning
from lys.decorators import avoidCircularReference

from ..interface import CanvasAnnotation, LineAnnotation, InfiniteLineAnnotation, RectAnnotation, RegionAnnotation, CrossAnnotation, FreeRegionAnnotation, TextAnnotation

_styles = {'solid': QtCore.Qt.SolidLine, 'dashed': QtCore.Qt.DashLine, 'dashdot': QtCore.Qt.DashDotLine, 'dotted': QtCore.Qt.DotLine, 'None': QtCore.Qt.NoPen}


def _setZ(obj, z):
    obj.setZValue(z - 100000)


class _PyqtgraphLineAnnotation(LineAnnotation):
    """Implementation of LineAnnotation for pyqtgraph"""

    def _initialize(self, pos, axis):
        self._obj = pg.LineSegmentROI(pos)
        self._obj.setPen(pg.mkPen(color='#000000'))
        self._obj.sigRegionChanged.connect(lambda obj: self.setPosition([[obj.pos()[0] + obj.listPoints()[0][0], obj.pos()[1] + obj.listPoints()[0][1]], [obj.pos()[0] + obj.listPoints()[1][0], obj.pos()[1] + obj.listPoints()[1][1]]]))
        self._axes = self.canvas().getAxes(axis)
        self._axes.addItem(self._obj)

    def _setPosition(self, pos):
        self._obj.movePoint(self._obj.getHandles()[0], pos[0], finish=False)
        self._obj.movePoint(self._obj.getHandles()[1], pos[1])

    def _setLineColor(self, color):
        self._obj.pen.setColor(QtGui.QColor(color))

    def _setLineStyle(self, style):
        self._obj.pen.setStyle(_styles[style])

    def _setLineWidth(self, width):
        self._obj.pen.setWidth(width)

    def _setZOrder(self, z):
        _setZ(self._obj, z)

    def _setVisible(self, visible):
        self._obj.setVisible(visible)

    def remove(self):
        self._axes.removeItem(self._obj)


class _PyqtgraphInfiniteLineAnnotation(InfiniteLineAnnotation):
    """Implementation of InfiniteLineAnnotation for pyqtgraph"""

    def _initialize(self, pos, orientation, axis):
        if orientation == 'vertical':
            self._obj = pg.InfiniteLine(pos, 90)
        else:
            self._obj = pg.InfiniteLine(pos, 0)
        self._obj.setMovable(True)
        self._obj.setPen(pg.mkPen(color='#000000'))
        self._obj.setVisible(True)
        self._obj.sigPositionChanged.connect(self._posChanged)
        self.canvas().getAxes(axis).addItem(self._obj)

    def _posChanged(self, line):
        self.setPosition(line.value())

    def _setPosition(self, pos):
        self._obj.setValue(pos)

    def _setLineColor(self, color):
        self._obj.pen.setColor(QtGui.QColor(color))

    def _setLineStyle(self, style):
        self._obj.pen.setStyle(_styles[style])

    def _setLineWidth(self, width):
        self._obj.pen.setWidth(width)

    def _setZOrder(self, z):
        _setZ(self._obj, z)

    def _setVisible(self, visible):
        self._obj.setVisible(visible)

    def remove(self):
        self.canvas().getAxes(self._axis).removeItem(self._obj)


class _PyqtgraphRectAnnotation(RectAnnotation):
    """Implementation of RectAnnotation for pyqtgraph"""

    def _initialize(self, pos, size, axis):
        self._obj = pg.RectROI(pos, size)
        self._obj.setPen(pg.mkPen(color='#000000'))
        self._obj.sigRegionChanged.connect(lambda roi: self.setRegion([[roi.pos()[0], roi.pos()[0] + roi.size()[0]], [roi.pos()[1], roi.pos()[1] + roi.size()[1]]]))
        self.canvas().getAxes(axis).addItem(self._obj)

    @avoidCircularReference
    def _setRegion(self, region):
        self._obj.setPos((region[0][0], region[1][0]))
        self._obj.setSize((region[0][1] - region[0][0], region[1][1] - region[1][0]))

    def _setLineColor(self, color):
        self._obj.pen.setColor(QtGui.QColor(color))

    def _setLineStyle(self, style):
        self._obj.pen.setStyle(_styles[style])

    def _setLineWidth(self, width):
        self._obj.pen.setWidth(width)

    def _setZOrder(self, z):
        _setZ(self._obj, z)

    def _setVisible(self, visible):
        self._obj.setVisible(visible)

    def remove(self):
        self.canvas().getAxes(self._axis).removeItem(self._obj)


class _PyqtgraphRegionAnnotation(RegionAnnotation):
    """Implementation of RegionAnnotation for pyqtgraph"""

    __list = {"horizontal": pg.LinearRegionItem.Horizontal, "vertical": pg.LinearRegionItem.Vertical}

    def _initialize(self, region, orientation, axis):
        self._obj = pg.LinearRegionItem(region, orientation=self.__list[orientation])
        self._obj.sigRegionChanged.connect(lambda roi: self.setRegion(roi.getRegion()))
        self.canvas().getAxes(axis).addItem(self._obj)

    def _setRegion(self, region):
        self._obj.setRegion(region)

    def _setLineColor(self, color):
        self._obj.lines[0].pen.setColor(QtGui.QColor(color))
        self._obj.lines[1].pen.setColor(QtGui.QColor(color))

    def _setLineStyle(self, style):
        self._obj.lines[0].pen.setStyle(_styles[style])
        self._obj.lines[1].pen.setStyle(_styles[style])

    def _setLineWidth(self, width):
        self._obj.lines[0].pen.setWidth(width)
        self._obj.lines[1].pen.setWidth(width)

    def _setZOrder(self, z):
        _setZ(self._obj, z)

    def _setVisible(self, visible):
        self._obj.setVisible(visible)

    def remove(self):
        self.canvas().getAxes(self._axis).removeItem(self._obj)


class _PyqtgraphFreeRegionAnnotation(FreeRegionAnnotation):
    """Implementation of FreeRegionAnnotation for pyqtgraph"""

    def _initialize(self, region, width, axis):
        pos1, pos2 = np.array(region[0]), np.array(region[1])
        d = pos2 - pos1
        v = np.array([-d[1], d[0]])
        pos = pos1 - width * v / np.linalg.norm(v) / 2
        self._obj = pg.RectROI(pos, size=(np.linalg.norm(d), width), angle=np.angle(d[0] + 1j * d[1], deg=True), movable=True, rotatable=True)
        handles = self._obj.getHandles()
        for h in handles:
            h.hide()
        self._obj.addScaleRotateHandle((0, 0.5), (1, 0.5))
        self._obj.addScaleRotateHandle((1, 0.5), (0, 0.5))
        self._obj.sigRegionChanged.connect(self._regionChanged)
        self.canvas().getAxes(axis).addItem(self._obj)

    @avoidCircularReference
    def _regionChanged(self, roi):
        p = np.array([roi.pos()[0], roi.pos()[1]])
        d = np.array((np.cos(roi.angle() / 180 * np.pi), np.sin(roi.angle() / 180 * np.pi)))
        v = np.array((-d[1], d[0]))
        self.setRegion([tuple(p + v * roi.size()[1] / 2), tuple(p + roi.size()[0] * d + v * roi.size()[1] / 2)])

    def _setRegion(self, region):
        self.__set(region, self.getWidth())

    def _setWidth(self, width):
        self.__set(self.getRegion(), width)

    @avoidCircularReference
    def __set(self, region, width):
        pos1, pos2 = np.array(region[0]), np.array(region[1])
        d = pos2 - pos1
        v = np.array([-d[1], d[0]])
        pos = pos1 - width * v / np.linalg.norm(v) / 2
        self._obj.setPos(pos)
        self._obj.setSize((np.linalg.norm(d), width))
        self._obj.setAngle(np.angle(d[0] + 1j * d[1], deg=True))

    def _setLineColor(self, color):
        self._obj.pen.setColor(QtGui.QColor(color))

    def _setLineStyle(self, style):
        self._obj.pen.setStyle(_styles[style])

    def _setLineWidth(self, width):
        self._obj.pen.setWidth(width)

    def _setZOrder(self, z):
        _setZ(self._obj, z)

    def _setVisible(self, visible):
        self._obj.setVisible(visible)

    def remove(self):
        self.canvas().getAxes(self._axis).removeItem(self._obj)


class _PyqtgraphCrossAnnotation(CrossAnnotation):
    """Implementation of CrossAnnotation for pyqtgraph"""

    def _initialize(self, position, axis):
        self._obj = _CrosshairItem(position)
        self._obj.sigRegionChanged.connect(lambda roi: self.setPosition(roi.getPosition()))
        self.canvas().getAxes(axis).addItem(self._obj)

    def _setPosition(self, pos):
        self._obj.lines[0].setValue(pos[1])
        self._obj.lines[1].setValue(pos[0])

    def _setLineColor(self, color):
        self._obj.lines[0].pen.setColor(QtGui.QColor(color))
        self._obj.lines[1].pen.setColor(QtGui.QColor(color))

    def _setLineStyle(self, style):
        self._obj.lines[0].pen.setStyle(_styles[style])
        self._obj.lines[1].pen.setStyle(_styles[style])

    def _setLineWidth(self, width):
        self._obj.lines[0].pen.setWidth(width)
        self._obj.lines[1].pen.setWidth(width)

    def _setZOrder(self, z):
        _setZ(self._obj, z)

    def _setVisible(self, visible):
        self._obj.setVisible(visible)

    def remove(self):
        self.canvas().getAxes(self._axis).removeItem(self._obj.lines[0])
        self.canvas().getAxes(self._axis).removeItem(self._obj.lines[1])


class _CrosshairItem(pg.GraphicsObject):
    sigRegionChangeFinished = QtCore.pyqtSignal(object)
    sigRegionChanged = QtCore.pyqtSignal(object)

    def __init__(self, values=(0, 1), pen=None):
        super().__init__()
        self.bounds = QtCore.QRectF()
        self.blockLineSignal = False
        self.moving = False
        self.mouseHovering = False
        self._bounds = None
        self.lines = [pg.InfiniteLine(values[0], 0), pg.InfiniteLine(values[1], 90)]
        for line in self.lines:
            line.setParentItem(self)
            line.sigPositionChangeFinished.connect(self.lineMoveFinished)
        self.lines[0].sigPositionChanged.connect(lambda: self.lineMoved(0))
        self.lines[1].sigPositionChanged.connect(lambda: self.lineMoved(1))
        self.setMovable(True)

    def getPosition(self):
        r = (self.lines[1].value(), self.lines[0].value())
        return r

    def setPosition(self, pos):
        if self.lines[0].value() == pos[0] and self.lines[1].value() == pos[1]:
            return
        self.blockLineSignal = True
        self.lines[0].setValue(pos[0])
        self.blockLineSignal = False
        self.lines[1].setValue(pos[1])
        self.lineMoved(0)
        self.lineMoved(1)
        self.lineMoveFinished()

    def setMovable(self, m):
        for line in self.lines:
            line.setMovable(m)
        self.movable = m
        self.setAcceptHoverEvents(m)

    def boundingRect(self):
        br = self.viewRect()  # bounds of containing ViewBox mapped to local coords.
        br = self.lines[0].boundingRect() & self.lines[1].boundingRect()
        br = br.normalized()

        if self._bounds != br:
            self._bounds = br
            self.prepareGeometryChange()

        return br

    def paint(self, p, *args):
        # p.drawEllipse(self.boundCircle())
        pass

    def lineMoved(self, i):
        if self.blockLineSignal:
            return
        self.prepareGeometryChange()
        self.sigRegionChanged.emit(self)

    def lineMoveFinished(self):
        self.sigRegionChangeFinished.emit(self)


class _PyqtgraphTextAnnotation(TextAnnotation):
    def _initialize(self, text, pos, axis):
        self._axis = axis
        self._xt, self._yt = "data", "data"
        self._obj = pg.TextItem(text=text, anchor=(0, 1))
        self.canvas().getAxes(axis).addItem(self._obj)
        self.canvas().axisRangeChanged.connect(self._refresh)

    def _refresh(self):
        self.setPosition(self.getPosition())

    def _setText(self, txt):
        self._obj.setText(txt)

    def __dataToAxes(self, x, y):
        rx, ry = self.canvas().getAxisRange(self._axis)
        return (x - rx[0]) / (rx[1] - rx[0]), (y - ry[0]) / (ry[1] - ry[0])

    def __axesToData(self, x, y):
        rx, ry = self.canvas().getAxisRange(self._axis)
        return rx[0] + (rx[1] - rx[0]) * x, ry[0] + (ry[1] - ry[0]) * y

    def _setPosition(self, pos):
        if self._xt == "data":
            x = pos[0]
        elif self._xt == "axes":
            x, _ = self.__axesToData(*pos)
        if self._yt == "data":
            y = pos[1]
        elif self._yt == "axes":
            _, y = self.__axesToData(*pos)
        self._obj.setPos(x, y)

    def _setTransform(self, transformation):
        if isinstance(transformation, str):
            xt = yt = transformation
        else:
            xt, yt = transformation
        xo, yo = self.getPosition()
        xd, yd = self.__axesToData(xo, yo)
        xa, ya = self.__dataToAxes(xo, yo)
        if self._xt != xt:
            self._xt = xt
            if xt == "data":
                x_new = xd
            else:
                x_new = xa
        else:
            x_new = xo
        if self._yt != yt:
            self._yt = yt
            if yt == "data":
                y_new = yd
            else:
                y_new = ya
        else:
            y_new = yo
        self.setPosition((x_new, y_new))

    def _setFont(self, family, size, color):
        self._obj.setColor(QtGui.QColor(color))
        self._obj.setFont(QtGui.QFont(family, size))

    def _setBoxStyle(self, style):
        warnings.warn("pyqtGraph does not support bounding box of text.", NotSupportedWarning)

    def _setBoxColor(self, faceColor, edgeColor):
        warnings.warn("pyqtGraph does not support bounding box of text.", NotSupportedWarning)

    def _setZOrder(self, z):
        _setZ(self._obj, z)

    def _setVisible(self, visible):
        self._obj.setVisible(visible)

    def remove(self):
        self.canvas().getAxes(self._axis).removeItem(self._obj)


class _PyqtgraphAnnotation(CanvasAnnotation):
    """Implementation of CanvasAnnotation for pyqtgraph"""

    def _addLineAnnotation(self, pos, axis):
        return _PyqtgraphLineAnnotation(self.canvas(), pos, axis)

    def _addInfiniteLineAnnotation(self, pos, type, axis):
        return _PyqtgraphInfiniteLineAnnotation(self.canvas(), pos, type, axis)

    def _addRectAnnotation(self, *args, **kwargs):
        return _PyqtgraphRectAnnotation(self.canvas(), *args, **kwargs)

    def _addRegionAnnotation(self, *args, **kwargs):
        return _PyqtgraphRegionAnnotation(self.canvas(), *args, **kwargs)

    def _addFreeRegionAnnotation(self, *args, **kwargs):
        return _PyqtgraphFreeRegionAnnotation(self.canvas(), *args, **kwargs)

    def _addCrossAnnotation(self, *args, **kwargs):
        return _PyqtgraphCrossAnnotation(self.canvas(), *args, **kwargs)

    def _addTextAnnotation(self, *args, **kwargs):
        return _PyqtgraphTextAnnotation(self.canvas(), *args, **kwargs)

    def _removeAnnotation(self, obj):
        obj.remove()
