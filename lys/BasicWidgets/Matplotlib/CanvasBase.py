from ..CanvasInterface import CanvasData
from ..CanvasInterface import *
from lys import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.contour import QuadContourSet
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import matplotlib as mpl

from .WaveData import _MatplotlibLine, _MatplotlibImage, _MatplotlibVector, _MatplotlibRGB, _MatplotlibContour

mpl.rc('image', cmap='gray')


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

    def _getAxesFrom(self, axis):
        return self.getAxes(axis)

    def getWaveDataFromArtist(self, artist):
        for i in self._Datalist:
            if i.id == artist.get_zorder():
                return i

    def constructContextMenu(self):
        return QMenu(self)


class FigureCanvasBase(_FigureCanvasBase):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self._data = _MatplotlibData(self)

    def __getattr__(self, key):
        if "_data" in self.__dict__:
            if hasattr(self._data, key):
                return getattr(self._data, key)
        return super().__getattr__(key)
