import pyqtgraph as pg

from lys.widgets import LysSubWindow
from ..CanvasInterface import CanvasBase, CanvasContextMenu, CanvasFont, CanvasKeyboardEvent, CanvasMouseEvent
from .AxisSettings import _pyqtGraphAxes, _pyqtGraphTicks
from .AxisLabelSettings import _PyqtgraphAxisLabel, _PyqtgraphTickLabel
from .AreaSettings import _PyqtGraphMargin, _PyqtGraphCanvasSize
from .WaveData import _PyqtgraphData
from .AnnotationData import _PyqtgraphAnnotation

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')


class _PyqtgraphMouseEvent(CanvasMouseEvent):
    def mapPosition(self, pos, axis):
        ax = self.canvas().getAxes(axis)
        p = ax.mapSceneToView(pos)
        return (p.x(), p.y())


class FigureCanvasBase(CanvasBase, pg.PlotWidget):
    def __init__(self, dpi=100):
        CanvasBase.__init__(self)
        pg.PlotWidget.__init__(self)
        self.__initFigure()
        self.updated.connect(self.update)
        self.__initCanvasParts()
        self.doubleClicked.connect(self.defModFunc)

    def __initFigure(self):
        self.fig = self.plotItem
        self.fig.canvas = None
        self.fig.showAxis('right')
        self.fig.showAxis('top')

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
        self.addCanvasPart(CanvasKeyboardEvent(self))
        self.addCanvasPart(_PyqtgraphMouseEvent(self))
        self.initCanvas.emit()

    def mouseReleaseEvent(self, event):
        self.mouseReleased.emit(event)
        super().mouseReleaseEvent(event)

    def mousePressEvent(self, event):
        self.mousePressed.emit(event)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        self.mouseMoved.emit(event)
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        self.keyPressed.emit(event)
        super().keyPressEvent(event)

    def defModFunc(self, tab='Axis'):
        from lys import ModifyWindow, Graph
        parent = self.parentWidget()
        while(parent is not None):
            if isinstance(parent, LysSubWindow):
                mod = ModifyWindow(self, parent, showArea=isinstance(parent, Graph))
                if isinstance(tab, str):
                    mod.selectTab(tab)
                break
            parent = parent.parentWidget()


"""
    def _onDrag(self, event, axis=0):
        if event.button() == Qt.LeftButton:
            if self._getMode() == "line":
                return self.__dragLine(event)
            if self._getMode() == "rect":
                return self.__dragRect(event)
        return super()._onDrag(event)

    def __dragLine(self, event):
        if event.isStart():
            self._roi_start = self.axes.mapSceneToView(event.scenePos())
            self.__roi = pg.LineSegmentROI(([0, 0], [1, 1]))
            self.__roi.setPen(pg.mkPen(color='#000000'))
            self.__roi.setPos(self._roi_start)
            self.__roi.setSize([0, 0])
            self.axes.addItem(self.__roi)
            self.__roi.show()
        elif event.isFinish():
            self.axes.removeItem(self.__roi)
            self.addLine([self._roi_start, self._roi_end])
        else:
            self._roi_end = self.axes.mapSceneToView(event.scenePos())
            self.__roi.setSize(self._roi_end - self._roi_start)
        event.accept()

    def __dragRect(self, event):
        if event.isStart():
            self._roi_start = self.axes.mapSceneToView(event.scenePos())
            self.__roi = pg.RectROI([0, 0], [1, 1])
            self.__roi.setPen(pg.mkPen(color='#000000'))
            self.__roi.setPos(self._roi_start)
            self.__roi.setSize([0, 0])
            self.axes.addItem(self.__roi)
            self.__roi.show()
        elif event.isFinish():
            self.axes.removeItem(self.__roi)
            self.addRect(self._roi_start, self._roi_end - self._roi_start)
        else:
            self._roi_end = self.axes.mapSceneToView(event.scenePos())
            self.__roi.setSize(self._roi_end - self._roi_start)
        event.accept()
"""
