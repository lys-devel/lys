from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg


from lys import *
from ..CanvasInterface import *
from ..CanvasInterface import CanvasBase, CanvasContextMenu, CanvasFont
from .AxisSettings import _pyqtGraphAxes, _pyqtGraphTicks
from .AxisLabelSettings import _PyqtgraphAxisLabel, _PyqtgraphTickLabel
from .AreaSettings import _PyqtGraphMargin, _PyqtGraphCanvasSize
from .WaveData import _PyqtgraphData
from .AnnotationData import _PyqtgraphAnnotation


class FigureCanvasBase(CanvasBase, pg.PlotWidget):
    def __init__(self, dpi=100):
        CanvasBase.__init__(self)
        pg.PlotWidget.__init__(self)
        self.__initFigure()
        self.updated.connect(self.update)
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

    def __initFigure(self):
        self.fig = self.plotItem
        self.fig.canvas = None
        self.fig.showAxis('right')
        self.fig.showAxis('top')

    def getWaveDataFromArtist(self, artist):
        for i in self._Datalist:
            if i.id == artist.get_zorder():
                return i

    def _onClick(self, event):
        if event.button() == Qt.LeftButton:
            if self.isRangeSelected():
                self.clearSelectedRange()
        return event.accept()

    def _onDrag(self, event, axis=0):
        if event.button() == Qt.LeftButton:
            pt = self.getAxes('BottomLeft').mapSceneToView(event.scenePos())
            if event.isStart():
                self._roi_start = (pt.x(), pt.y())
                self._roi_end = (pt.x(), pt.y())
            else:
                self._roi_end = (pt.x(), pt.y())
            self.setSelectedRange([self._roi_start, self._roi_end])
            return event.accept()
        return event.ignore()


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
