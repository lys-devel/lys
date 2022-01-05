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


class _FigureCanvasBase(pg.PlotWidget, AbstractCanvasBase):
    def __init__(self, dpi=100):
        AbstractCanvasBase.__init__(self)
        super().__init__()
        self.fig = self.plotItem
        self.fig.canvas = None
        self.fig.showAxis('right')
        self.fig.showAxis('top')

    def _draw(self):
        self.update()

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


class FigureCanvasBase(_FigureCanvasBase):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self._data = _PyqtgraphData(self)

    def __getattr__(self, key):
        if "_data" in self.__dict__:
            if hasattr(self._data, key):
                return getattr(self._data, key)
        return super().__getattr__(key)
