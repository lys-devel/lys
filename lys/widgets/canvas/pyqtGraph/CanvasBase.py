import weakref
import pyqtgraph as pg

from lys.Qt import QtGui

from ..interface import CanvasBase, CanvasContextMenu, CanvasFont, CanvasKeyboardEvent, CanvasMouseEvent, CanvasFocusEvent, CanvasUtilities
from .AxisSettings import _pyqtGraphAxes, _pyqtGraphTicks
from .AxisLabelSettings import _PyqtgraphAxisLabel, _PyqtgraphTickLabel
from .AreaSettings import _PyqtGraphMargin, _PyqtGraphCanvasSize
from .WaveData import _PyqtgraphData
from .AnnotationData import _PyqtgraphAnnotation
from .LegendSettings import _PyqtgraphLegend

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')


class _PyqtgraphMouseEvent(CanvasMouseEvent):
    def mapPosition(self, event, axis):
        ax = self.canvas().getAxes(axis)
        if isinstance(event, QtGui.QMouseEvent):
            pos = event.pos()
        else:
            pos = event.scenePos()
        p = ax.mapSceneToView(pos)
        return (p.x(), p.y())


class FigureCanvasBase(CanvasBase, pg.PlotWidget):
    def __init__(self, dpi=100):
        CanvasBase.__init__(self)
        pg.PlotWidget.__init__(self)
        self._flg = True
        self.__initFigure()
        self.updated.connect(self.update)
        self.__initCanvasParts()
        self.scene().sigMouseHover.connect(self._hover)
        self._helper = _dragHelper(self)
        self.getAxes('BottomLeft').mouseDragEvent = self._helper.onDrag

    def __initFigure(self):
        self.fig = self.plotItem
        self.fig.canvas = None
        self.fig.showAxis('right')
        self.fig.showAxis('top')

    def getPlotItem(self):
        return self.fig

    def __initCanvasParts(self):
        self.addCanvasPart(_PyqtgraphData(self))
        self.addCanvasPart(_pyqtGraphAxes(self))
        self.addCanvasPart(_pyqtGraphTicks(self))
        self.addCanvasPart(CanvasContextMenu(self))
        self.addCanvasPart(CanvasFont(self))
        self.addCanvasPart(_PyqtgraphAxisLabel(self))
        self.addCanvasPart(_PyqtgraphTickLabel(self))
        self.addCanvasPart(_PyqtGraphMargin(self))
        self.addCanvasPart(_PyqtGraphCanvasSize(self))
        self.addCanvasPart(_PyqtgraphAnnotation(self))
        self.addCanvasPart(CanvasUtilities(self))
        self.addCanvasPart(CanvasKeyboardEvent(self))
        self.addCanvasPart(_PyqtgraphMouseEvent(self))
        self.addCanvasPart(CanvasFocusEvent(self))
        self.addCanvasPart(_PyqtgraphLegend(self))
        self.initCanvas.emit()

    def _hover(self, list):
        self._flg = True
        for item in list:
            if isinstance(item, (pg.ROI, pg.InfiniteLine)):
                self._flg = False

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.mouseReleased.emit(event)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self._flg:  # ignore when the event is processed by pyqtgraph
            self.mousePressed.emit(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.mouseMoved.emit(event)

    def keyPressEvent(self, event):
        self.keyPressed.emit(event)
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focused.emit(event)

    def _onDrag(self, event):
        self.mouseMoved.emit(event)
        return event.accept()


class _dragHelper:
    def __init__(self, obj):
        self._obj = weakref.ref(obj)

    def onDrag(self, event):
        event.accept()
