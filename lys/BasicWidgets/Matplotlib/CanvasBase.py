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
    axisChanged = pyqtSignal(str)

    def __init__(self, dpi=100):
        self.fig = Figure(dpi=dpi)
        AbstractCanvasBase.__init__(self)
        super().__init__(self.fig)
        self._axes = self.fig.add_subplot(111)  # TODO #This line takes 0.3s for each image.
        self._axes.minorticks_on()
        self._axes.xaxis.set_picker(15)
        self._axes.yaxis.set_picker(15)
        self._axes_tx = None
        self._axes_ty = None
        self._axes_txy = None

    def _draw(self):
        super().draw()

    def _getAxesFrom(self, axis):
        return self.__getAxes(axis)

    def __getAxes(self, axis):
        self.__enableAxes(axis)
        if axis == "BottomLeft":
            return self._axes
        if axis == "TopLeft":
            return self._axes_ty
        if axis == "BottomRight":
            return self._axes_tx
        if axis == "TopRight":
            return self._axes_txy

    def __enableAxes(self, axis):
        if axis == "TopLeft" and self._axes_ty is None:
            self._axes_ty = self._axes.twiny()
            self._axes_ty.spines['left'].set_visible(False)
            self._axes_ty.spines['right'].set_visible(False)
            self._axes_ty.xaxis.set_picker(15)
            self._axes_ty.yaxis.set_picker(15)
            self._axes_ty.minorticks_on()
            self.axisChanged.emit('Top')
        if axis == 'BottomRight' and self._axes_tx is None:
            self._axes_tx = self.axes.twinx()
            self._axes_tx.spines['top'].set_visible(False)
            self._axes_tx.spines['bottom'].set_visible(False)
            self._axes_tx.xaxis.set_picker(15)
            self._axes_tx.yaxis.set_picker(15)
            self._axes_tx.minorticks_on()
            self.axisChanged.emit('Right')
        if axis == "TopRight" and self._axes_txy is None:
            self.__enableAxes("TopLeft")
            self.__enableAxes("BottomRight")
            self._axes_txy = self.axes_tx.twiny()
            self._axes_txy.get_xaxis().set_tick_params(top=False, labeltop=False, which="both")
            self._axes_txy.xaxis.set_picker(15)
            self._axes_txy.yaxis.set_picker(15)

    def getAxes(self, axis='Left'):
        if axis in ['BottomLeft', 'BottomRight', 'TopLeft', 'TopRight']:
            return self.__getAxes(axis)
        ax = axis
        if ax in ['Left', 'Bottom']:
            return self._axes
        if ax == 'Top':
            if self._axes_ty is not None:
                return self._axes_ty
            else:
                return self._axes_txy
        if ax == 'Right':
            if self._axes_tx is not None:
                return self._axes_tx
            else:
                return self._axes_txy

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
