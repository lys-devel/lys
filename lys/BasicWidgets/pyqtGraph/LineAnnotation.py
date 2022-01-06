import pyqtgraph as pg
from LysQt.QtCore import Qt
from LysQt.QtGui import QColor
from ..CanvasInterface import LineAnnotation, InfiniteLineAnnotation

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

    def _setColor(self, color):
        self._obj.pen.setColor(QColor(color))

    def _setStyle(self, style):
        self._obj.pen.setStyle(_styles[style])

    def _setWidth(self, width):
        self._obj.pen.setWidth(width)

    def _setZOrder(self, z):
        self._obj.setZValue(z)


class _PyqtgraphInfiniteLineAnnotation(InfiniteLineAnnotation):

    def __init__(self, canvas, pos, type, axis):
        super().__init__(canvas, pos, type, axis)
        if type == 'vertical':
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

    def _setColor(self, color):
        self._obj.pen.setColor(QColor(color))

    def _setStyle(self, style):
        self._obj.pen.setStyle(_styles[style])

    def _setWidth(self, width):
        self._obj.pen.setWidth(width)

    def _setZOrder(self, z):
        self._obj.setZValue(z)
