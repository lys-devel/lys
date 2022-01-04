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
    axisChanged = pyqtSignal(str)
    pgRangeChanged = pyqtSignal(str)

    def __init__(self, dpi=100):
        AbstractCanvasBase.__init__(self)
        super().__init__()
        self.__resizing = False
        self.fig = self.plotItem
        self.fig.canvas = None
        self.fig.showAxis('right')
        self.fig.showAxis('top')
        self.__initAxes()

    def _draw(self):
        self.update()

    def _getAxesFrom(self, axis):
        return self.__getAxes(axis)

    def __updateViews(self):
        self.__resizing = True
        self._axes_tx_com.setGeometry(self._axes.sceneBoundingRect())
        #self.axes_tx_com.linkedViewChanged(self.axes, self.axes_tx_com.XAxis)

        self._axes_ty_com.setGeometry(self._axes.sceneBoundingRect())
        #self.axes_ty_com.linkedViewChanged(self.axes, self.axes_ty_com.YAxis)

        self._axes_txy_com.setGeometry(self._axes.sceneBoundingRect())
        #self.axes_txy_com.linkedViewChanged(self.axes, self.axes_txy_com.XAxis)
        #self.axes_txy_com.linkedViewChanged(self.axes, self.axes_txy_com.YAxis)
        self.__resizing = False

    def __viewRangeChanged(self, axis):
        if not self.__resizing:
            self.pgRangeChanged.emit(axis)

    def __initAxes(self):
        self._axes = self.fig.vb

        self._axes_tx = None
        self._axes_tx_com = pg.ViewBox()
        self.fig.scene().addItem(self._axes_tx_com)
        self.fig.getAxis('right').linkToView(self._axes_tx_com)
        self._axes_tx_com.setXLink(self._axes)
        self._axes_tx_com.setYLink(self._axes)

        self._axes_ty = None
        self._axes_ty_com = pg.ViewBox()
        self.fig.scene().addItem(self._axes_ty_com)
        self.fig.getAxis('top').linkToView(self._axes_ty_com)
        self._axes_ty_com.setXLink(self._axes)
        self._axes_ty_com.setYLink(self._axes)

        self._axes_txy = None
        self._axes_txy_com = pg.ViewBox()
        self.fig.scene().addItem(self._axes_txy_com)
        self._axes_txy_com.setYLink(self._axes_tx_com)
        self._axes_txy_com.setXLink(self._axes_ty_com)

        self.fig.getAxis('top').setStyle(showValues=False)
        self.fig.getAxis('right').setStyle(showValues=False)

        self._axes.sigResized.connect(self.__updateViews)
        self._axes.sigRangeChanged.connect(lambda: self.__viewRangeChanged("Left"))
        self._axes.sigRangeChanged.connect(lambda: self.__viewRangeChanged("Bottom"))
        self._axes_txy_com.sigRangeChanged.connect(lambda: self.__viewRangeChanged("Top"))
        self._axes_txy_com.sigRangeChanged.connect(lambda: self.__viewRangeChanged("Right"))

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
            self._axes_ty_com.setXLink(None)
            self._axes_ty = self.axes_ty_com
            self.fig.getAxis('top').setStyle(showValues=True)
            self.axisChanged.emit('Top')
        if axis == "BottomRight" and self._axes_tx is None:
            self._axes_tx_com.setYLink(None)
            self._axes_tx = self.axes_tx_com
            self.fig.getAxis('right').setStyle(showValues=True)
            self.axisChanged.emit('Right')
        if axis == "TopRight" and self._axes_txy is None:
            self._axes_ty_com.setXLink(None)
            self._axes_tx_com.setYLink(None)
            self._axes_txy = self._axes_txy_com
            self.fig.getAxis('top').setStyle(showValues=True)
            self.fig.getAxis('right').setStyle(showValues=True)
            self.axisChanged.emit('Right')
            self.axisChanged.emit('Top')

    def getAxes(self, axis='Left'):
        if axis in ["BottomLeft", "BottomRight", "TopLeft", "TopRight"]:
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
