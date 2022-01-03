from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg


from lys import *
from ..CanvasInterface import *
from .WaveData import _PyqtgraphLine, _PyqtgraphImage, _PyqtgraphRGB, _PyqtgraphContour


class FigureCanvasBase(pg.PlotWidget, AbstractCanvasBase):
    axisChanged = pyqtSignal(str)
    pgRangeChanged = pyqtSignal(str)

    def __init__(self, dpi=100):
        AbstractCanvasBase.__init__(self)
        super().__init__()
        self.__resizing = False
        self.__initAxes()
        self.fig.canvas = None

    def _draw(self):
        self.update()

    def _getAxesFrom(self, axis):
        return self.__getAxes(axis)

    def __updateViews(self):
        self.__resizing = True
        self.axes_tx_com.setGeometry(self.axes.sceneBoundingRect())
        #self.axes_tx_com.linkedViewChanged(self.axes, self.axes_tx_com.XAxis)

        self.axes_ty_com.setGeometry(self.axes.sceneBoundingRect())
        #self.axes_ty_com.linkedViewChanged(self.axes, self.axes_ty_com.YAxis)

        self.axes_txy_com.setGeometry(self.axes.sceneBoundingRect())
        #self.axes_txy_com.linkedViewChanged(self.axes, self.axes_txy_com.XAxis)
        #self.axes_txy_com.linkedViewChanged(self.axes, self.axes_txy_com.YAxis)
        self.__resizing = False

    def __viewRangeChanged(self, axis):
        if not self.__resizing:
            self.pgRangeChanged.emit(axis)

    def __initAxes(self):
        self.fig = self.plotItem
        self.axes = self.fig.vb
        self.fig.showAxis('right')
        self.fig.showAxis('top')

        self.axes_tx = None
        self.axes_tx_com = pg.ViewBox()
        self.fig.scene().addItem(self.axes_tx_com)
        self.fig.getAxis('right').linkToView(self.axes_tx_com)
        self.axes_tx_com.setXLink(self.axes)
        self.axes_tx_com.setYLink(self.axes)

        self.axes_ty = None
        self.axes_ty_com = pg.ViewBox()
        self.fig.scene().addItem(self.axes_ty_com)
        self.fig.getAxis('top').linkToView(self.axes_ty_com)
        self.axes_ty_com.setXLink(self.axes)
        self.axes_ty_com.setYLink(self.axes)

        self.axes_txy = None
        self.axes_txy_com = pg.ViewBox()
        self.fig.scene().addItem(self.axes_txy_com)
        self.axes_txy_com.setYLink(self.axes_tx_com)
        self.axes_txy_com.setXLink(self.axes_ty_com)

        self.fig.getAxis('top').setStyle(showValues=False)
        self.fig.getAxis('right').setStyle(showValues=False)

        self.axes.sigResized.connect(self.__updateViews)
        self.axes.sigRangeChanged.connect(lambda: self.__viewRangeChanged("Left"))
        self.axes.sigRangeChanged.connect(lambda: self.__viewRangeChanged("Bottom"))
        self.axes_txy_com.sigRangeChanged.connect(lambda: self.__viewRangeChanged("Top"))
        self.axes_txy_com.sigRangeChanged.connect(lambda: self.__viewRangeChanged("Right"))

    def __getAxes(self, axis):
        if axis == "BottomLeft":
            return self.axes
        if axis == "TopLeft":
            if self.axes_ty is None:
                self.axes_ty_com.setXLink(None)
                self.axes_ty = self.axes_ty_com
                self.fig.getAxis('top').setStyle(showValues=True)
                self.axisChanged.emit('Top')
            return self.axes_ty
        if axis == "BottomRight":
            if self.axes_tx is None:
                self.axes_tx_com.setYLink(None)
                self.axes_tx = self.axes_tx_com
                self.fig.getAxis('right').setStyle(showValues=True)
                self.axisChanged.emit('Right')
            return self.axes_tx
        if axis == "TopRight":
            if self.axes_txy is None:
                self.axes_ty_com.setXLink(None)
                self.axes_tx_com.setYLink(None)
                self.axes_txy = self.axes_txy_com
                self.fig.getAxis('top').setStyle(showValues=True)
                self.fig.getAxis('right').setStyle(showValues=True)
                self.axisChanged.emit('Right')
                self.axisChanged.emit('Top')
            return self.axes_txy

    def getAxes(self, axis='Left'):
        if axis in ["BottomLeft", "BottomRight", "TopLeft", "TopRight"]:
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
        return _PyqtgraphLine(self, wave, axis)

    def _append2d(self, wave, axis):
        return _PyqtgraphImage(self, wave, axis)

    def _append3d(self, wave, axis):
        return _PyqtgraphRGB(self, wave, axis)

    def _appendContour(self, wav, axis):
        return _PyqtgraphContour(self, wav, axis)

    def _remove(self, data):
        ax = self.__getAxes(data.axis)
        ax.removeItem(data._obj)

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
