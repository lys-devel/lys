import numpy as np

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


class FigureCanvasBase(FigureCanvas, AbstractCanvasBase):
    axisChanged = pyqtSignal(str)

    def __init__(self, dpi=100):
        self.fig = Figure(dpi=dpi)
        AbstractCanvasBase.__init__(self)
        super().__init__(self.fig)
        self.axes = self.fig.add_subplot(111)  # TODO #This line takes 0.3s for each image.
        self.axes.minorticks_on()
        self.axes.xaxis.set_picker(15)
        self.axes.yaxis.set_picker(15)
        self.axes_tx = None
        self.axes_ty = None
        self.axes_txy = None

    def _draw(self):
        super().draw()

    def _getAxesFrom(self, axis):
        return self.__getAxes(axis)

    def __getAxes(self, axis):
        if axis == "BottomLeft":
            return self.axes
        if axis == "TopLeft":
            if self.axes_ty is None:
                self.axes_ty = self.axes.twiny()
                self.axes_ty.spines['left'].set_visible(False)
                self.axes_ty.spines['right'].set_visible(False)
                self.axes_ty.xaxis.set_picker(15)
                self.axes_ty.yaxis.set_picker(15)
                self.axes_ty.minorticks_on()
                self.axisChanged.emit('Top')
            return self.axes_ty
        if axis == "BottomRight":
            if self.axes_tx is None:
                self.axes_tx = self.axes.twinx()
                self.axes_tx.spines['top'].set_visible(False)
                self.axes_tx.spines['bottom'].set_visible(False)
                self.axes_tx.xaxis.set_picker(15)
                self.axes_tx.yaxis.set_picker(15)
                self.axes_tx.minorticks_on()
                self.axisChanged.emit('Right')
            return self.axes_tx
        if axis == "TopRight":
            if self.axes_txy is None:
                self.__getAxes("TopLeft")
                self.__getAxes("BottomRight")
                self.axes_txy = self.axes_tx.twiny()
                self.axes_txy.get_xaxis().set_tick_params(top=False, labeltop=False, which="both")
                self.axes_txy.xaxis.set_picker(15)
                self.axes_txy.yaxis.set_picker(15)
            return self.axes_txy

    def getAxes(self, axis='Left'):
        if axis in ['BottomLeft', 'BottomRight', 'TopLeft', 'TopRight']:
            return self.__getAxes(axis)
        ax = axis
        if ax in ['Left', 'Bottom']:
            return self.axes
        if ax == 'Top':
            if self.axes_ty is not None:
                return self.axes_ty
            else:
                return self.axes_txy
        if ax == 'Right':
            if self.axes_tx is not None:
                return self.axes_tx
            else:
                return self.axes_txy

    def _append1d(self, wave, axis):
        return _MatplotlibLine(self, wave, axis)

    def _append2d(self, wave, axis):
        return _MatplotlibImage(self, wave, axis)

    def _append3d(self, wave, axis):
        return _MatplotlibRGB(self, wave, axis)

    def _appendContour(self, wav, axis):
        return _MatplotlibContour(self, wav, axis)

    def _appendVectorField(self, wav, axis):
        return _MatplotlibVector(self, wav, axis)

    def _remove(self, data):
        if isinstance(data._obj, QuadContourSet):
            for o in data._obj.collections:
                o.remove()
        else:
            data._obj.remove()

    def getWaveDataFromArtist(self, artist):
        for i in self._Datalist:
            if i.id == artist.get_zorder():
                return i

    def constructContextMenu(self):
        return QMenu(self)
