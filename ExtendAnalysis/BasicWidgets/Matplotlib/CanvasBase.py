#!/usr/bin/env python
import weakref, sys, os
from enum import Enum
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure, SubplotParams
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import colors

import matplotlib as mpl
mpl.rc('image',cmap='gray')

from ExtendAnalysis import *
from ExtendAnalysis import LoadFile
from ..CanvasInterface import *

class FigureCanvasBase(FigureCanvas,AbstractCanvasBase):
    axisChanged=pyqtSignal(str)
    def __init__(self, dpi=100):
        self.fig=Figure(dpi=dpi)
        AbstractCanvasBase.__init__(self)
        super().__init__(self.fig)
        self.axes = self.fig.add_subplot(111)#TODO #This line takes 0.3s for each image.
        self.axes.minorticks_on()
        self.axes.xaxis.set_picker(15)
        self.axes.yaxis.set_picker(15)
        self.axes_tx=None
        self.axes_ty=None
        self.axes_txy=None
    def _draw(self):
        super().draw()
    def _getAxesFrom(self,axis):
        return self.__getAxes(axis)
    def __getAxes(self,axis):
        if axis==Axis.BottomLeft:
            return self.axes
        if axis==Axis.TopLeft:
            if self.axes_ty is None:
                self.axes_ty=self.axes.twiny()
                self.axes_ty.spines['left'].set_visible(False)
                self.axes_ty.spines['right'].set_visible(False)
                self.axes_ty.xaxis.set_picker(15)
                self.axes_ty.yaxis.set_picker(15)
                self.axes_ty.minorticks_on()
                self.axisChanged.emit('Top')
            return self.axes_ty
        if axis==Axis.BottomRight:
            if self.axes_tx is None:
                self.axes_tx=self.axes.twinx()
                self.axes_tx.spines['top'].set_visible(False)
                self.axes_tx.spines['bottom'].set_visible(False)
                self.axes_tx.xaxis.set_picker(15)
                self.axes_tx.yaxis.set_picker(15)
                self.axes_tx.minorticks_on()
                self.axisChanged.emit('Right')
            return self.axes_tx
        if axis==Axis.TopRight:
            if self.axes_txy is None:
                self.axes_txy=self.axes.twinx().twiny()
                self.axisChanged.emit('Right')
                self.axisChanged.emit('Top')
                self.axes_txy.xaxis.set_picker(15)
                self.axes_txy.yaxis.set_picker(15)
                self.axes_txy.minorticks_on()
            return self.axes_txy
    def _append1d(self,xdata,ydata,axis,zorder):
        ax=self.__getAxes(axis)
        line, = ax.plot(xdata,ydata,picker=5)
        line.set_zorder(zorder)
        return line, ax
    def calcExtent2D(self,wav,offset):
        xstart=wav.x[0]
        xend=wav.x[len(wav.x)-1]
        ystart=wav.y[0]
        yend=wav.y[len(wav.y)-1]
        if not offset[2]==0:
            xstart*=offset[2]
            xend*=offset[2]
        if not offset[3]==0:
            ystart*=offset[3]
            yend*=offset[3]
        xstart=xstart+offset[0]
        xend=xend+offset[0]
        ystart=ystart+offset[1]
        yend=yend+offset[1]
        dx=(xend-xstart+1)/wav.data.shape[1]
        dy=(yend-ystart+1)/wav.data.shape[0]
        return (xstart-dx/2,xend+dx/2,yend+dy/2,ystart-dy/2)
    def _append2d(self,wave,offset,axis,zorder):
        ax=self.__getAxes(axis)
        im=ax.imshow(wave.data.T,aspect='auto',extent=self.calcExtent2D(wave,offset),picker=True)
        im.set_zorder(zorder)
        return im, ax
    def AppendContour(self,wav,offset=(0,0,0,0)):
        ax=self.__getAxes(Axis.BottomLeft)
        ext=self.calcExtent2D(wav,offset)
        obj=ax.contour(wav.data[::-1,:],[0.5],extent=ext,colors=['red'])
        return obj
    def _remove(self,data):
        data.obj.remove()
    def _setZOrder(self,obj,z):
        obj.set_zorder(z)

    def getWaveDataFromArtist(self,artist):
        for i in self._Datalist:
            if i.id==artist.get_zorder():
                return i
    def axesName(self,axes):
        if axes==self.axes:
            return 'Bottom Left'
        if axes==self.axes_tx:
            return 'Bottom Right'
        if axes==self.axes_ty:
            return 'Top Left'
        else:
            return 'Top Right'
    def _reorder(self):
        n1=0
        n2=0
        for d in self._Datalist:
            if d.wave.data.ndim==1:
                d.id=-2000+n1
                n1+=1
            if d.wave.data.ndim==2:
                d.id=-5000+n2
                n2+=1
            d.obj.set_zorder(d.id)
        self.draw()
    def constructContextMenu(self):
        return QMenu(self)

    # DataHidableCanvasBase
    def _isVisible(self,obj):
        return obj.get_visible()
    def _setVisible(self,obj,b):
        obj.set_visible(b)