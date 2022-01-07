from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg


from lys import *
from ..CanvasInterface import *
from .WaveData import _PyqtgraphLine, _PyqtgraphImage, _PyqtgraphRGB, _PyqtgraphContour


class _PyqtgraphData(CanvasData):
    def _append1d(self, wave, axis):
        return _PyqtgraphLine(self.canvas(), wave, axis)

    def _append2d(self, wave, axis):
        return _PyqtgraphImage(self.canvas(), wave, axis)

    def _append3d(self, wave, axis):
        return _PyqtgraphRGB(self.canvas(), wave, axis)

    def _appendContour(self, wav, axis):
        return _PyqtgraphContour(self.canvas(), wav, axis)

    def _remove(self, data):
        ax = self.canvas().getAxes(data.getAxis())
        ax.removeItem(data._obj)


class FigureCanvasBase(CanvasBase, pg.PlotWidget):
    def __init__(self, dpi=100):
        CanvasBase.__init__(self)
        pg.PlotWidget.__init__(self)
        self.fig = self.plotItem
        self.fig.canvas = None
        self.fig.showAxis('right')
        self.fig.showAxis('top')
        self.updated.connect(self.update)
        self.addCanvasPart(_PyqtgraphData(self))

    def getWaveDataFromArtist(self, artist):
        for i in self._Datalist:
            if i.id == artist.get_zorder():
                return i

    def constructContextMenu(self):
        return QMenu(self)

    def _onClick(self, event):
        event.accept()

    def _onDrag(self, event):
        event.ignore()
