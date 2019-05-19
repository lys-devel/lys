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

class FigureCanvasBase(FigureCanvas,CanvasBaseBase):
    def __init__(self, dpi=100):
        self.fig=Figure(dpi=dpi)
        CanvasBaseBase.__init__(self)
        super().__init__(self.fig)
        self.axes = self.fig.add_subplot(111)#TODO #This line takes 0.3s for each image.
        self.axes.minorticks_on()
        self.axes.xaxis.set_picker(15)
        self.axes.yaxis.set_picker(15)
        self.axes_tx=None
        self.axes_ty=None
        self.axes_txy=None
        self.__lisaxis=[]
    def _draw(self):
        super().draw()
    def addAxisChangeListener(self,listener):
        self.__lisaxis.append(weakref.ref(listener))
    def __emitAxisChanged(self,axis):
        for l in self.__lisaxis:
            if l() is not None:
                l().OnAxisChanged(axis)
            else:
                self.__lisaxis.remove(l)
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
                self.__emitAxisChanged('Top')
            return self.axes_ty
        if axis==Axis.BottomRight:
            if self.axes_tx is None:
                self.axes_tx=self.axes.twinx()
                self.axes_tx.spines['top'].set_visible(False)
                self.axes_tx.spines['bottom'].set_visible(False)
                self.axes_tx.xaxis.set_picker(15)
                self.axes_tx.yaxis.set_picker(15)
                self.axes_tx.minorticks_on()
                self.__emitAxisChanged('Right')
            return self.axes_tx
        if axis==Axis.TopRight:
            if self.axes_txy is None:
                self.axes_txy=self.axes.twinx().twiny()
                self.__emitAxisChanged('Right')
                self.__emitAxisChanged('Top')
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
        im=ax.imshow(wave.data,aspect='auto',extent=self.calcExtent2D(wave,offset),picker=True)
        im.set_zorder(zorder)
        return im, ax
    def AppendContour(self,wav,offset=(0,0,0,0)):
        ax=self.__getAxes(Axis.BottomLeft)
        ext=self.calcExtent2D(wav,offset)
        obj=ax.contour(wav.data[::-1,:],[0.5],extent=ext,colors=['red'])
        return obj
    def _remove(self,data):
        data.obj.remove()
    def getWaveData(self,dim=None):
        if dim is None:
            return self._Datalist
        res=[]
        for d in self._Datalist:
            if d.wave.data.ndim==1 and dim==1:
                res.append(d)
            if d.wave.data.ndim>=2 and dim==2:
                res.append(d)
        return res
    def getLines(self):
        return self.getWaveData(1)
    def getImages(self):
        return self.getWaveData(2)
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

class DataSelectableCanvas(FigureCanvasBase):
    def __init__(self,dpi):
        super().__init__(dpi)
        self.__indexes=[[],[],[],[]]
        self.__listener=[]
    def setSelectedIndexes(self,dim,indexes):
        if hasattr(indexes, '__iter__'):
            list=indexes
        else:
            list=[indexes]
        self.__indexes[dim]=list
        self._emitDataSelected()
    def getSelectedIndexes(self,dim):
        return self.__indexes[dim]
    def getDataFromIndexes(self,dim,indexes):
        res=[]
        if hasattr(indexes, '__iter__'):
            list=indexes
        else:
            list=[indexes]
        for i in list:
            for d in self.getWaveData(dim):
                if d.id==i:
                    res.append(d)
        return res
    def _emitDataSelected(self):
        for l in self.__listener:
            if l() is not None:
                l().OnDataSelected()
            else:
                self.__listener.remove(l)
    def _findIndex(self,id):
        res=-1
        for d in self._Datalist:
            if d.id==id:
                res=self._Datalist.index(d)
        return res
    @saveCanvas
    def moveItem(self,list,target=None):
        tar=eval(str(target))
        for l in list:
            n=self._findIndex(l)
            item_n=self._Datalist[n]
            self._Datalist.remove(item_n)
            if tar is not None:
                self._Datalist.insert(self._findIndex(tar)+1,item_n)
            else:
                self._Datalist.insert(0,item_n)
        self._reorder()
        self.dataChanged.emit()
    def addDataSelectionListener(self,listener):
        self.__listener.append(weakref.ref(listener))

class DataHidableCanvas(DataSelectableCanvas):
    def saveAppearance(self):
        super().saveAppearance()
        data=self.getWaveData()
        for d in data:
            d.appearance['Visible']=d.obj.get_visible()
    def loadAppearance(self):
        super().loadAppearance()
        data=self.getWaveData()
        for d in data:
            if 'Visible' in d.appearance:
                d.obj.set_visible(d.appearance['Visible'])
    @saveCanvas
    def hideData(self,dim,indexes):
        dat=self.getDataFromIndexes(dim,indexes)
        for d in dat:
            d.obj.set_visible(False)
        self.draw()
    @saveCanvas
    def showData(self,dim,indexes):
        dat=self.getDataFromIndexes(dim,indexes)
        for d in dat:
            d.obj.set_visible(True)
        self.draw()

class OffsetAdjustableCanvas(DataHidableCanvas):
    @saveCanvas
    def setOffset(self,offset,indexes):
        data=self.getDataFromIndexes(None,indexes)
        for d in data:
            d.offset=offset
            self.OnWaveModified(d.wave)
    def getOffset(self,indexes):
        res=[]
        data=self.getDataFromIndexes(None,indexes)
        for d in data:
            res.append(d.offset)
        return res
