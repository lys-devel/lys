from ..CanvasInterface import CanvasData
from ..CanvasInterface import *
from lys import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.contour import QuadContourSet
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .WaveData import _MatplotlibLine, _MatplotlibImage, _MatplotlibVector, _MatplotlibRGB, _MatplotlibContour


class _MatplotlibData(CanvasData):
    def _append1d(self, wave, axis):
        return _MatplotlibLine(self.canvas(), wave, axis)

    def _append2d(self, wave, axis):
        return _MatplotlibImage(self.canvas(), wave, axis)

    def _append3d(self, wave, axis):
        return _MatplotlibRGB(self.canvas(), wave, axis)

    def _appendContour(self, wav, axis):
        return _MatplotlibContour(self.canvas(), wav, axis)

    def _appendVectorField(self, wav, axis):
        return _MatplotlibVector(self.canvas(), wav, axis)

    def _remove(self, data):
        if isinstance(data._obj, QuadContourSet):
            for o in data._obj.collections:
                o.remove()
        else:
            data._obj.remove()


class _FigureCanvasBase(FigureCanvas, AbstractCanvasBase):
    def __init__(self, dpi=100):
        self.fig = Figure(dpi=dpi)
        AbstractCanvasBase.__init__(self)
        super().__init__(self.fig)

    def _draw(self):
        super().draw()

    def getWaveDataFromArtist(self, artist):
        for i in self._Datalist:
            if i.id == artist.get_zorder():
                return i

    def constructContextMenu(self):
        return QMenu(self)


class CanvasBase(_FigureCanvasBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__parts = []

    def addCanvasPart(self, part):
        self.__parts.append(part)

    def __getattr__(self, key):
        for part in self.__parts:
            if hasattr(part, key):
                return getattr(part, key)
        return super().__getattr__(key)


class FigureCanvasBase(CanvasBase):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.addCanvasPart(_MatplotlibData(self))
