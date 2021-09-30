#!/usr/bin/env python
import weakref
import sys
import os
import warnings
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
from lys import *
from ..CanvasInterface import *

warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')


def _suppressNumpyWarnings(func):
    def wrapper(*args, **kwargs):
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')
            warnings.filterwarnings('ignore', r'invalid value encountered in reduce')
            return func(*args, **kwargs)
    return wrapper


class FigureCanvasBase(pg.PlotWidget, AbstractCanvasBase):
    axisChanged = pyqtSignal(str)

    def __init__(self, dpi=100):
        AbstractCanvasBase.__init__(self)
        super().__init__()
        self.__initAxes()
        self.fig.canvas = None
        self.npen = 0

    def RestoreSize(self):
        pass

    def _draw(self):
        self.update()

    def _getAxesFrom(self, axis):
        return self.__getAxes(axis)

    def __updateViews(self):
        self.axes_tx_com.setGeometry(self.axes.sceneBoundingRect())
        self.axes_tx_com.linkedViewChanged(self.axes, self.axes_tx_com.XAxis)

        self.axes_ty_com.setGeometry(self.axes.sceneBoundingRect())
        self.axes_ty_com.linkedViewChanged(self.axes, self.axes_ty_com.YAxis)

        self.axes_txy_com.setGeometry(self.axes.sceneBoundingRect())
        self.axes_txy_com.linkedViewChanged(self.axes, self.axes_txy_com.XAxis)
        self.axes_txy_com.linkedViewChanged(self.axes, self.axes_txy_com.YAxis)

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

    def __getAxes(self, axis):
        if axis == Axis.BottomLeft:
            return self.axes
        if axis == Axis.TopLeft:
            if self.axes_ty is None:
                self.axes_ty_com.setXLink(None)
                self.axes_ty = self.axes_ty_com
                self.fig.getAxis('right').setStyle(showValues=False)
                self.axisChanged.emit('Top')
            return self.axes_ty
        if axis == Axis.BottomRight:
            if self.axes_tx is None:
                self.axes_tx_com.setYLink(None)
                self.axes_tx = self.axes_tx_com
                self.fig.getAxis('top').setStyle(showValues=False)
                self.axisChanged.emit('Right')
            return self.axes_tx
        if axis == Axis.TopRight:
            if self.axes_txy is None:
                self.axes_ty_com.setXLink(None)
                self.axes_tx_com.setYLink(None)
                self.axes_txy = self.axes_txy_com
                self.fig.getAxis('top').setStyle(showValues=False)
                self.fig.getAxis('right').setStyle(showValues=False)
                self.axisChanged.emit('Right')
                self.axisChanged.emit('Top')
            return self.axes_txy

    def _nextPen(self):
        list = ["#17becf", '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', "#7f7f7f"]
        self.npen += 1
        return pg.mkPen(list[self.npen % 9], width=2)

    @_suppressNumpyWarnings
    def _append1d(self, xdata, ydata, axis, zorder):
        ax = self.__getAxes(axis)
        obj = pg.PlotDataItem(x=xdata, y=ydata, pen=self._nextPen())
        ax.addItem(obj)
        obj.setZValue(zorder)
        return obj, ax

    @_suppressNumpyWarnings
    def _append2d(self, wave, offset, axis, zorder):
        ax = self.__getAxes(axis)
        im = pg.ImageItem(image=wave.data)
        shift, mag = self.calcExtent2D(wave, offset)
        im.scale(*mag)
        im.translate(*shift)
        ax.addItem(im)
        im.setZValue(zorder)
        return im, ax

    @_suppressNumpyWarnings
    def _append3d(self, wave, offset, axis, zorder):
        ax = self.__getAxes(axis)
        im = pg.ImageItem(image=wave.data, levels=(0, 1))
        shift, mag = self.calcExtent2D(wave, offset)
        im.scale(*mag)
        im.translate(*shift)
        ax.addItem(im)
        im.setZValue(zorder)
        return im, ax

    @_suppressNumpyWarnings
    def _appendContour(self, wav, offset, axis, zorder):
        ax = self.__getAxes(axis)
        shift, mag = self.calcExtent2D(wav, offset)
        obj = pg.IsocurveItem(data=wav.data, level=0.5, pen='r')
        obj.scale(*mag)
        obj.translate(*shift)
        ax.addItem(obj)
        obj.setZValue(zorder)
        return obj, ax

    def calcExtent2D(self, wav, offset):
        xstart = wav.x[0]
        xend = wav.x[len(wav.x) - 1]
        ystart = wav.y[0]
        yend = wav.y[len(wav.y) - 1]

        xmag_orig = (xend - xstart)
        ymag_orig = (yend - ystart)
        if not offset[2] == 0:
            xstart *= offset[2]
            xend *= offset[2]
        if not offset[3] == 0:
            ystart *= offset[3]
            yend *= offset[3]

        dx = (xend - xstart) / (len(wav.x) - 1)
        dy = (yend - ystart) / (len(wav.y) - 1)

        xstart = xstart - dx / 2
        xend = xend + dx / 2
        ystart = ystart - dy / 2
        yend = yend + dy / 2

        xmag = (xend - xstart) / len(wav.x)
        ymag = (yend - ystart) / len(wav.y)
        xshift = xstart
        yshift = ystart
        return ((xshift + offset[0]) / xmag, (yshift + offset[1]) / ymag), (xmag, ymag)

    def _remove(self, data):
        data.axes.removeItem(data.obj)

    def _setZOrder(self, obj, z):
        obj.setZValue(z)

    def getWaveDataFromArtist(self, artist):
        for i in self._Datalist:
            if i.id == artist.get_zorder():
                return i

    def axesName(self, axes):
        if axes == self.axes:
            return 'Bottom Left'
        if axes == self.axes_tx:
            return 'Bottom Right'
        if axes == self.axes_ty:
            return 'Top Left'
        else:
            return 'Top Right'

    def constructContextMenu(self):
        return QMenu(self)

    def _onClick(self, event):
        event.accept()

    def _onDrag(self, event):
        event.ignore()

    # DataHidableCanvasBase
    def _isVisible(self, obj):
        return obj.isVisible()

    def _setVisible(self, obj, b):
        obj.setVisible(b)
