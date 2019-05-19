#!/usr/bin/env python
import weakref, sys, os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
from ExtendAnalysis import *
from ExtendAnalysis import LoadFile
from ..CanvasInterface import *

class FigureCanvasBase(pg.PlotWidget,CanvasBaseBase):
    def __init__(self, dpi=100):
        CanvasBaseBase.__init__(self)
        super().__init__()
        self.__initAxes()
        self.fig.canvas=None
        self.__lisaxis=[]
        self.npen=0
    def RestoreSize(self):
        pass

    def _draw(self):
        self.update()
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
    def __updateViews(self):
        self.axes_tx_com.setGeometry(self.axes.sceneBoundingRect())
        self.axes_tx_com.linkedViewChanged(self.axes, self.axes_tx_com.XAxis)

        self.axes_ty_com.setGeometry(self.axes.sceneBoundingRect())
        self.axes_ty_com.linkedViewChanged(self.axes, self.axes_ty_com.YAxis)

        self.axes_txy_com.setGeometry(self.axes.sceneBoundingRect())
        self.axes_txy_com.linkedViewChanged(self.axes, self.axes_txy_com.XAxis)
        self.axes_txy_com.linkedViewChanged(self.axes, self.axes_txy_com.YAxis)
    def __initAxes(self):
        self.fig=self.plotItem
        self.axes = self.fig.vb
        self.fig.showAxis('right')
        self.fig.showAxis('top')

        self.axes_tx=None
        self.axes_tx_com=pg.ViewBox()
        self.fig.scene().addItem(self.axes_tx_com)
        self.fig.getAxis('right').linkToView(self.axes_tx_com)
        self.axes_tx_com.setXLink(self.axes)
        self.axes_tx_com.setYLink(self.axes)

        self.axes_ty=None
        self.axes_ty_com=pg.ViewBox()
        self.fig.scene().addItem(self.axes_ty_com)
        self.fig.getAxis('top').linkToView(self.axes_ty_com)
        self.axes_ty_com.setXLink(self.axes)
        self.axes_ty_com.setYLink(self.axes)

        self.axes_txy=None
        self.axes_txy_com=pg.ViewBox()
        self.fig.scene().addItem(self.axes_txy_com)
        self.axes_txy_com.setYLink(self.axes_tx_com)
        self.axes_txy_com.setXLink(self.axes_ty_com)

        self.fig.getAxis('top').setStyle(showValues=False)
        self.fig.getAxis('right').setStyle(showValues=False)

        self.axes.sigResized.connect(self.__updateViews)
    def __getAxes(self,axis):
        if axis==Axis.BottomLeft:
            return self.axes
        if axis==Axis.TopLeft:
            if self.axes_ty is None:
                self.axes_ty_com.setXLink(None)
                self.axes_ty=self.axes_ty_com
                self.fig.getAxis('right').setStyle(showValues=False)
            return self.axes_ty
        if axis==Axis.BottomRight:
            if self.axes_tx is None:
                self.axes_tx_com.setYLink(None)
                self.axes_tx=self.axes_tx_com
                self.fig.getAxis('top').setStyle(showValues=False)
            return self.axes_tx
        if axis==Axis.TopRight:
            if self.axes_txy is None:
                self.axes_ty_com.setXLink(None)
                self.axes_tx_com.setYLink(None)
                self.axes_txy=self.axes_txy_com
                self.fig.getAxis('top').setStyle(showValues=False)
                self.fig.getAxis('right').setStyle(showValues=False)
            return self.axes_txy
    def _nextPen(self):
        list=[ "#17becf", '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', "#7f7f7f"]
        self.npen+=1
        return pg.mkPen(list[self.npen%9],width=2)
    def _append1d(self,xdata,ydata,axis,zorder):
        ax=self.__getAxes(axis)
        obj=pg.PlotDataItem(x=xdata,y=ydata,pen=self._nextPen())
        ax.addItem(obj)
        obj.setZValue(zorder)
        return obj, ax
    def _append2d(self,wave,offset,axis,zorder):
        ax=self.__getAxes(axis)
        im=pg.ImageItem(image=wave.data)
        shift,mag=self.calcExtent2D(wave,offset)
        im.scale(*mag)
        im.translate(*shift)
        ax.addItem(im)
        im.setZValue(zorder)
        return im, ax
    def calcExtent2D(self,wav,offset):
        xstart=wav.x[0]
        xend=wav.x[len(wav.x)-1]
        ystart=wav.y[0]
        yend=wav.y[len(wav.y)-1]

        xmag_orig=(xend-xstart)
        ymag_orig=(yend-ystart)
        if not offset[2]==0:
            xstart*=offset[2]
            xend*=offset[2]
        if not offset[3]==0:
            ystart*=offset[3]
            yend*=offset[3]

        dx=(xend-xstart)/(len(wav.x)-1)
        dy=(yend-ystart)/(len(wav.y)-1)

        xstart=xstart-dx/2
        xend=xend+dx/2
        ystart=ystart-dy/2
        yend=yend+dy/2

        xmag=(xend-xstart)/len(wav.x)
        ymag=(yend-ystart)/len(wav.y)
        xshift=xstart
        yshift=ystart
        return ((xshift+offset[0])/xmag,(yshift+offset[1])/ymag), (xmag,ymag)
    def AppendContour(self,wav,offset=(0,0,0,0)):
        ax=self.__getAxes(Axis.BottomLeft)
        ext=self.calcExtent2D(wav,offset)
        obj=ax.contour(wav.data[::-1,:],[0.5],extent=ext,colors=['red'])
        return obj
    def _remove(self,data):
        data.axes.removeItem(data.obj)

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
    def _onClick(self,event):
        event.accept()
    def _onDrag(self, event):
        event.ignore()

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
            d.appearance['Visible']=d.obj.isVisible()
    def loadAppearance(self):
        super().loadAppearance()
        data=self.getWaveData()
        for d in data:
            if 'Visible' in d.appearance:
                d.obj.setVisible(d.appearance['Visible'])
    @saveCanvas
    def hideData(self,dim,indexes):
        dat=self.getDataFromIndexes(dim,indexes)
        for d in dat:
            d.obj.setVisible(False)
        self.draw()
    @saveCanvas
    def showData(self,dim,indexes):
        dat=self.getDataFromIndexes(dim,indexes)
        for d in dat:
            d.obj.setVisible(True)
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
