import pyqtgraph as pg
from LysQt.QtCore import Qt, pyqtSignal, QRectF
from LysQt.QtGui import QColor, QTransform
from ..CanvasInterface import LineAnnotation, InfiniteLineAnnotation, RectAnnotation, RegionAnnotation, CrossAnnotation

_styles = {'solid': Qt.SolidLine, 'dashed': Qt.DashLine, 'dashdot': Qt.DashDotLine, 'dotted': Qt.DotLine, 'None': Qt.NoPen}


class _PyqtgraphLineAnnotation(LineAnnotation):
    def __init__(self, canvas, pos, axis):
        super().__init__(canvas, pos, axis)
        self._obj = pg.LineSegmentROI(pos)
        self._obj.setPen(pg.mkPen(color='#000000'))
        canvas.getAxes(axis).addItem(self._obj)
        # TODO : set signal emitted when position is changed by user.

    def _addAnnotCallback(self, obj, callback):
        obj.sigRegionChanged.connect(lambda obj: callback([[obj.pos()[0] + obj.listPoints()[0][0], obj.pos()[0] + obj.listPoints()[1][0]], [obj.pos()[1] + obj.listPoints()[0][1], obj.pos()[1] + obj.listPoints()[1][1]]]))
        obj.sigRegionChanged.emit(obj)

    def _setPosition(self, pos):
        self._obj.getHandles()[0].setPos(pos[0][0] - self._obj.pos()[0], pos[1][0] - self._obj.pos()[1])
        self._obj.getHandles()[1].setPos(pos[0][1] - self._obj.pos()[0], pos[1][1] - self._obj.pos()[1])

    def _setLineColor(self, color):
        self._obj.pen.setColor(QColor(color))

    def _setLineStyle(self, style):
        self._obj.pen.setStyle(_styles[style])

    def _setLineWidth(self, width):
        self._obj.pen.setWidth(width)

    def _setZOrder(self, z):
        self._obj.setZValue(z)

    def _setVisible(self, visible):
        self._obj.setVisible(visible)


class _PyqtgraphInfiniteLineAnnotation(InfiniteLineAnnotation):
    def __init__(self, canvas, pos, orientation, axis):
        super().__init__(canvas, pos, orientation, axis)
        if orientation == 'vertical':
            self._obj = pg.InfiniteLine(pos, 90)
        else:
            self._obj = pg.InfiniteLine(pos, 0)
        self._obj.setMovable(True)
        self._obj.setPen(pg.mkPen(color='#000000'))
        self._obj.setVisible(True)
        canvas.getAxes(axis).addItem(self._obj)
        # TODO : set signal emitted when position is changed by user.

    def _addAnnotCallback(self, obj, callback):
        obj.sigPositionChanged.connect(lambda line: callback(line.value()))
        obj.sigPositionChanged.emit(obj)

    def _setPosition(self, pos):
        self._obj.setValue(pos)

    def _setLineColor(self, color):
        self._obj.pen.setColor(QColor(color))

    def _setLineStyle(self, style):
        self._obj.pen.setStyle(_styles[style])

    def _setLineWidth(self, width):
        self._obj.pen.setWidth(width)

    def _setZOrder(self, z):
        self._obj.setZValue(z)

    def _setVisible(self, visible):
        self._obj.setVisible(visible)


class _PyqtgraphRectAnnotation(RectAnnotation):
    def __init__(self, canvas, pos, size, axis):
        super().__init__(canvas, pos, size, axis)
        self._obj = pg.RectROI(pos, size)
        self._obj.setPen(pg.mkPen(color='#000000'))
        canvas.getAxes(axis).addItem(self._obj)
        # TODO : set signal emitted when position is changed by user.

    def _addAnnotCallback(self, obj, callback):
        obj.sigRegionChanged.connect(lambda roi: callback([[roi.pos()[0], roi.pos()[0] + roi.size()[0]], [roi.pos()[1], roi.pos()[1] + roi.size()[1]]]))
        obj.sigRegionChanged.emit(obj)

    def _setPosition(self, x, y):
        self._obj.setPos((x, y))

    def _setSize(self, w, h):
        self._obj.setSize((w, h))

    def _setLineColor(self, color):
        self._obj.pen.setColor(QColor(color))

    def _setLineStyle(self, style):
        self._obj.pen.setStyle(_styles[style])

    def _setLineWidth(self, width):
        self._obj.pen.setWidth(width)

    def _setZOrder(self, z):
        self._obj.setZValue(z)

    def _setVisible(self, visible):
        self._obj.setVisible(visible)


class _PyqtgraphRegionAnnotation(RegionAnnotation):
    __list = {"horizontal": pg.LinearRegionItem.Horizontal, "vertical": pg.LinearRegionItem.Vertical}

    def __init__(self, canvas, region, orientation, axis):
        super().__init__(canvas, region, orientation, axis)
        self._obj = pg.LinearRegionItem(region, orientation=self.__list[orientation])
        canvas.getAxes(axis).addItem(self._obj)
        # TODO : set signal emitted when position is changed by user.

    def _addAnnotCallback(self, obj, callback):
        obj.sigRegionChanged.connect(lambda roi: callback(roi.getRegion()))
        obj.sigRegionChanged.emit(obj)

    def _setRegion(self, region):
        self._obj.setRegion(region)

    def _setLineColor(self, color):
        self._obj.lines[0].pen.setColor(QColor(color))
        self._obj.lines[1].pen.setColor(QColor(color))

    def _setLineStyle(self, style):
        self._obj.lines[0].pen.setStyle(_styles[style])
        self._obj.lines[1].pen.setStyle(_styles[style])

    def _setLineWidth(self, width):
        self._obj.lines[0].pen.setWidth(width)
        self._obj.lines[1].pen.setWidth(width)

    def _setZOrder(self, z):
        self._obj.setZValue(z)

    def _setVisible(self, visible):
        self._obj.setVisible(visible)


class _PyqtgraphCrossAnnotation(CrossAnnotation):
    def __init__(self, canvas, position, axis):
        super().__init__(canvas, position, axis)
        self._obj = _CrosshairItem(position)
        canvas.getAxes(axis).addItem(self._obj)
        # TODO : set signal emitted when position is changed by user.

    def _addAnnotCallback(self, obj, callback):
        obj.sigRegionChanged.connect(lambda roi: callback(roi.getPosition()))

    def _setPosition(self, pos):
        self._obj.lines[0].setValue(pos[1])
        self._obj.lines[1].setValue(pos[0])

    def _setLineColor(self, color):
        self._obj.lines[0].pen.setColor(QColor(color))
        self._obj.lines[1].pen.setColor(QColor(color))

    def _setLineStyle(self, style):
        self._obj.lines[0].pen.setStyle(_styles[style])
        self._obj.lines[1].pen.setStyle(_styles[style])

    def _setLineWidth(self, width):
        self._obj.lines[0].pen.setWidth(width)
        self._obj.lines[1].pen.setWidth(width)

    def _setZOrder(self, z):
        self._obj.setZValue(z)

    def _setVisible(self, visible):
        self._obj.setVisible(visible)


class _CrosshairItem(pg.GraphicsObject):
    sigRegionChangeFinished = pyqtSignal(object)
    sigRegionChanged = pyqtSignal(object)

    def __init__(self, values=(0, 1), pen=None):
        super().__init__()
        self.bounds = QRectF()
        self.blockLineSignal = False
        self.moving = False
        self.mouseHovering = False
        self._bounds = None
        self.lines = [pg.InfiniteLine(angle=0), pg.InfiniteLine(angle=90)]
        tr = QTransform()
        tr.scale(1, -1)
        self.lines[0].setTransform(tr)
        self.lines[1].setTransform(tr)
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
        for l in self.lines:
            l.setMovable(m)
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
