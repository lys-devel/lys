#!/usr/bin/env python
import weakref, sys, os
from enum import Enum
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
from ExtendAnalysis import *
from ExtendAnalysis import LoadFile

def _saveCanvas(func):
    import functools
    @functools.wraps(func)
    def wrapper(*args,**kwargs):
        if args[0].saveflg:
            res=func(*args,**kwargs)
        else:
            args[0].saveflg=True
            res=func(*args,**kwargs)
            args[0].Save()
            args[0].saveflg=False
        return res
    return wrapper
def _notSaveCanvas(func):
    import functools
    @functools.wraps(func)
    def wrapper(*args,**kwargs):
        saved=args[0].saveflg
        args[0].saveflg=True
        res=func(*args,**kwargs)
        args[0].saveflg=saved
        return res
    return wrapper
class Axis(Enum):
    BottomLeft=1
    TopLeft=2
    BottomRight=3
    TopRight=4
class WaveData(object):
    def __init__(self,wave,obj,axis,idn,appearance,offset=(0,0,0,0),zindex=0):
        self.wave=wave
        self.obj=obj
        self.axis=axis
        self.id=idn
        self.appearance=appearance
        self.offset=offset
        self.zindex=zindex
class FigureCanvasBase(pg.PlotWidget):
    waveAppended=pyqtSignal(int)
    def __init__(self, dpi=100):
        super().__init__()
        self.__initAxes()
        self.fig.canvas=None
        self.__listener=[]
        self.__lisaxis=[]
        self._Datalist=[]
        return
        self.axes.minorticks_on()
        self.axes.xaxis.set_picker(15)
        self.axes.yaxis.set_picker(15)
        self.__lisdraw=[]
        self.drawflg=False
        self.__loadFlg=False
        self.savef=None
    def RestoreSize(self):
        pass
    def setSaveFunction(self,func):
        self.savef=weakref.WeakMethod(func)
    def Save(self):
        print("Save is not implemented.")
        return
        if (not self.__loadFlg) and (self.savef is not None):
            self.savef()()
    @_saveCanvas
    def OnWaveModified(self,wave):
        flg=False
        self.__loadFlg=True
        self.EnableDraw(False)
        self.saveAppearance()
        for d in self._Datalist:
            if wave==d.wave:
                d.obj.remove()
                self._Datalist.remove(d)
                self._Append(wave,d.axis,d.id,appearance=d.appearance,offset=d.offset,zindex=d.zindex,reuse=True)
                flg=True
        self.loadAppearance()
        self.EnableDraw(True)
        if(flg):
            self.draw()
        self.__loadFlg=False
    def IsDrawEnabled(self):
        return self.drawflg
    def EnableDraw(self,b):
        self.drawflg=b
    def EnableSave(self,b):
        self.saveflg=b
    def draw(self):
        if self.drawflg is not None:
            if not self.drawflg:
                return
        try:
            super().draw()
            self.__emitAfterDraw()
        except Exception:
            pass
    def addAxisChangeListener(self,listener):
        self.__lisaxis.append(weakref.ref(listener))
    def addAfterDrawListener(self,listener):
        self.__lisdraw.append(weakref.ref(listener))
    def __emitAfterDraw(self):
        for l in self.__lisdraw:
            if l() is not None:
                l().OnAfterDraw()
            else:
                self.__lisdraw.remove(l)
    def __emitAxisChanged(self,axis):
        for l in self.__lisaxis:
            if l() is not None:
                l().OnAxisChanged(axis)
            else:
                self.__lisaxis.remove(l)
    def _getAxesFrom(self,axis):
        return self.__getAxes(axis)

    def __updateViews(self):
        self.axes_tx.setGeometry(self.axes.sceneBoundingRect())
        self.axes_tx.linkedViewChanged(self.axes, self.axes_tx.XAxis)

        self.axes_ty.setGeometry(self.axes.sceneBoundingRect())
        self.axes_ty.linkedViewChanged(self.axes, self.axes_ty.YAxis)

        self.axes_txy.setGeometry(self.axes.sceneBoundingRect())
        self.axes_txy.linkedViewChanged(self.axes, self.axes_txy.XAxis)
        self.axes_txy.linkedViewChanged(self.axes, self.axes_txy.YAxis)
    def __initAxes(self):
        self.fig=self.plotItem
        self.axes = self.fig.vb
        self.fig.showAxis('right')
        self.fig.showAxis('top')

        self.axes_tx=pg.ViewBox()
        self.fig.scene().addItem(self.axes_tx)
        self.fig.getAxis('right').linkToView(self.axes_tx)
        self.axes_tx.setXLink(self.axes)
        #self.axes_tx.xaxis.set_picker(15)
        #self.axes_tx.yaxis.set_picker(15)
        #self.axes_tx.minorticks_on()

        self.axes_ty=pg.ViewBox()
        self.fig.scene().addItem(self.axes_ty)
        self.fig.getAxis('top').linkToView(self.axes_ty)
        self.axes_ty.setYLink(self.axes)
        #self.axes_tx.xaxis.set_picker(15)
        #self.axes_tx.yaxis.set_picker(15)
        #self.axes_tx.minorticks_on()

        self.axes_txy=pg.ViewBox()
        self.fig.scene().addItem(self.axes_txy)
        self.axes_txy.setYLink(self.axes_tx)
        self.axes_txy.setXLink(self.axes_ty)
        #self.axes_tx.xaxis.set_picker(15)
        #self.axes_tx.yaxis.set_picker(15)
        #self.axes_tx.minorticks_on()

        self.axes.sigResized.connect(self.__updateViews)
    def __getAxes(self,axis):
        if axis==Axis.BottomLeft:
            return self.axes
        if axis==Axis.TopLeft:
            return self.axes_ty
        if axis==Axis.BottomRight:
            return self.axes_tx
        if axis==Axis.TopRight:
            return self.axes_txy

    def Append(self,wave,axis=Axis.BottomLeft,id=None,appearance=None,offset=(0,0,0,0),zindex=0):
        ax=self.__getAxes(axis)
        if isinstance(wave,Wave):
            wav=wave
        else:
            wav=LoadFile.load(wave)
        if appearance is None:
            ids=self._Append(wav,ax,id,{},offset,zindex)
        else:
            ids=self._Append(wav,ax,id,dict(appearance),offset,zindex)
        return ids
    @_saveCanvas
    def _Append(self,wav,ax,id,appearance,offset,zindex=0, reuse=False):
        if wav.data.ndim==1:
            ids=self._Append1D(wav,ax,id,appearance,offset)
        if wav.data.ndim==2:
            ids=self._Append2D(wav,ax,id,appearance,offset)
        if wav.data.ndim==3:
            ids=self._Append3D(wav,ax,id,appearance,offset,zindex)
        if not reuse:
            wav.addModifiedListener(self.OnWaveModified)
        self._emitDataChanged()
        self.waveAppended.emit(ids)
        if appearance is not None:
            self.loadAppearance()
        return ids
    def _Append1D(self,wav,ax,ID,appearance,offset):
        if wav.x.ndim==0:
            xdata=np.arange(len(wav.data))
            ydata=np.array(wav.data)
        else:
            xdata=np.array(wav.x)
            ydata=np.array(wav.data)
        if not offset[2]==0.0:
            xdata=xdata*offset[2]
        if not offset[3]==0.0:
            ydata=ydata*offset[3]
        xdata=xdata+offset[0]
        ydata=ydata+offset[1]
        obj=pg.PlotCurveItem(x=xdata,y=ydata)
        ax.addItem(obj)
        if ID is None:
            id=-2000+len(self.getLines())
        else:
            id=ID
        obj.setZValue(id)
        self._Datalist.insert(id+2000,WaveData(wav,obj,ax,id,appearance,offset))
        return 0
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

    def _Append2D(self,wav,ax,ID,appearance,offset):
        im=ax.imshow(wav.data,aspect='auto',extent=self.calcExtent2D(wav,offset),picker=True)
        if ID is None:
            id=-5000+len(self.getImages())
        else:
            id=ID
        im.set_zorder(id)
        d=WaveData(wav,im,ax,id,appearance,offset)
        self._Datalist.insert(id+5000,d)
        if len(appearance.keys()) == 0:
            self.setColormap('gray',id)
        return id
    def AppendContour(self,wav,offset=(0,0,0,0)):
        ax=self.__getAxes(Axis.BottomLeft)
        ext=self.calcExtent2D(wav,offset)
        obj=ax.contour(wav.data[::-1,:],[0.5],extent=ext,colors=['red'])
        return obj
    def _Append3D(self,wav,ax,ID,appearance,offset,z):
        xstart=wav.x[0]+offset[0]
        xend=wav.x[len(wav.x)-1]+offset[0]
        ystart=wav.y[0]+offset[1]
        yend=wav.y[len(wav.y)-1]+offset[1]
        if not offset[2]==0:
            xstart*=offset[2]
            xend*=offset[2]
        if not offset[3]==0:
            ystart*=offset[3]
            yend*=offset[3]
        im=ax.imshow(wav.getSlicedImage(z),aspect='auto',extent=(xstart,xend,ystart,yend),picker=True)
        if ID is None:
            id=-5000+len(self.getImages())
        else:
            id=ID
        im.set_zorder(id)
        self._Datalist.insert(id+5000,WaveData(wav,im,ax,id,appearance,offset,z))
        self.setColormap('gray',id)
        return id
    @_saveCanvas
    def Remove(self,indexes):
        if hasattr(indexes, '__iter__'):
            list=indexes
        else:
            list=[indexes]
        for i in list:
            for d in self._Datalist:
                if i==d.id:
                    d.obj.remove()
                    self._Datalist.remove(d)
        self._emitDataChanged()
        self.draw()
    @_saveCanvas
    def Clear(self):
        for d in self._Datalist:
            d.obj.remove()
        self._Datalist.clear()
        self._emitDataChanged()
        self.draw()
    def addDataChangeListener(self,listener):
        self.__listener.append(weakref.ref(listener))
    def _emitDataChanged(self):
        for l in self.__listener:
            if l() is not None:
                l().OnDataChanged()
            else:
                self.__listener.remove(l)
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
    def SaveAsDictionary(self,dictionary,path):
        print("Save as dictionary is not implemented.")
        return
        i=0
        dic={}
        self.saveAppearance()
        for data in self._Datalist:
            dic[i]={}
            fname=data.wave.FileName()
            if fname is not None:
                dic[i]['File']=os.path.relpath(data.wave.FileName(),path).replace('\\','/')
            else:
                dic[i]['File']=None
            if data.axis==self.axes:
                axis=1
            if data.axis==self.axes_ty:
                axis=2
            if data.axis==self.axes_tx:
                axis=3
            if data.axis==self.axes_txy:
                axis=4
            dic[i]['Axis']=axis
            dic[i]['Appearance']=str(data.appearance)
            dic[i]['Offset']=str(data.offset)
            dic[i]['ZIndex']=str(data.zindex)
            i+=1
        dictionary['Datalist']=dic
    def LoadFromDictionary(self,dictionary,path):
        self.__loadFlg=True
        i=0
        sdir=pwd()
        cd(path)
        if 'Datalist' in dictionary:
            dic=dictionary['Datalist']
            while i in dic:
                p=dic[i]['File']
                if p is None:
                    i+=1
                    continue
                axis=dic[i]['Axis']
                if axis==1:
                    axis=Axis.BottomLeft
                if axis==2:
                    axis=Axis.TopLeft
                if axis==3:
                    axis=Axis.BottomRight
                if axis==4:
                    axis=Axis.TopRight
                if 'Appearance' in dic[i]:
                    ap=eval(dic[i]['Appearance'])
                else:
                    ap={}
                if 'Offset' in dic[i]:
                    offset=eval(dic[i]['Offset'])
                if 'ZIndex' in dic[i]:
                    zi=eval(dic[i]['ZIndex'])
                else:
                    offset=(0,0,0,0)
                self.Append(p,axis,appearance=ap,offset=offset,zindex=zi)
                i+=1
        self.loadAppearance()
        self.__loadFlg=False
        cd(sdir)
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
    def saveAppearance(self):
        pass
    def loadAppearance(self):
        pass
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
    @_saveCanvas
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
        self._emitDataChanged()
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
    @_saveCanvas
    def hideData(self,dim,indexes):
        dat=self.getDataFromIndexes(dim,indexes)
        for d in dat:
            d.obj.set_visible(False)
        self.draw()
    @_saveCanvas
    def showData(self,dim,indexes):
        dat=self.getDataFromIndexes(dim,indexes)
        for d in dat:
            d.obj.set_visible(True)
        self.draw()

class OffsetAdjustableCanvas(DataHidableCanvas):
    @_saveCanvas
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