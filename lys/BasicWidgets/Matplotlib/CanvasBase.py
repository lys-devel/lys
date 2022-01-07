from ..CanvasInterface import CanvasData, CanvasBase
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


class FigureCanvasBase(CanvasBase, FigureCanvas):
    def __init__(self, dpi=100):
        self.fig = Figure(dpi=dpi)
        CanvasBase.__init__(self)
        FigureCanvas.__init__(self, self.fig)
        self.updated.connect(self.draw)
        self.addCanvasPart(_MatplotlibData(self))

    def getWaveDataFromArtist(self, artist):
        for i in self._Datalist:
            if i.id == artist.get_zorder():
                return i

    def constructContextMenu(self):
        return QMenu(self)
