#!/usr/bin/env python
import random, weakref, gc, sys, os
from collections import namedtuple
from ColorWidgets import *
import numpy as np
from enum import Enum
from ExtendType import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure, SubplotParams
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.widgets import RectangleSelector
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import lines, markers, ticker
from GraphWindow import *

class WaveData(object):
    def __init__(self,wave,obj,axis,idn,appearance,offset=(0,0,0,0)):
        self.wave=wave
        self.obj=obj
        self.axis=axis
        self.id=idn
        self.appearance=appearance
        self.offset=offset
class FigureCanvasBase(FigureCanvas):
    def __init__(self, dpi=100):
        self.fig=Figure(dpi=dpi)
        super().__init__(self.fig)
        self.axes = self.fig.add_subplot(111)
        self.axes.minorticks_on()
        self.axes_tx=None
        self.axes_ty=None
        self.axes_txy=None
        self._Datalist=[]
        self.__listener=[]
        self.__lisaxis=[]

        Wave.AddWaveModificationListener(self)
    def OnWaveModified(self,wave):
        flg=False
        self.saveAppearance()
        for d in self._Datalist:
            if wave==d.wave:
                d.obj.remove()
                self._Datalist.remove(d)
                self._Append(wave,d.axis,d.id,appearance=d.appearance,offset=d.offset)
                flg=True
        self.loadAppearance()
        if(flg):
            self.draw()
    def draw(self):
        try:
            super().draw()
        except Exception:
            pass
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
                self.axes_ty.minorticks_on()
                self.__emitAxisChanged('Top')
            return self.axes_ty
        if axis==Axis.BottomRight:
            if self.axes_tx is None:
                self.axes_tx=self.axes.twinx()
                self.axes_tx.spines['top'].set_visible(False)
                self.axes_tx.spines['bottom'].set_visible(False)
                self.axes_tx.minorticks_on()
                self.__emitAxisChanged('Right')
            return self.axes_tx
        if axis==Axis.TopRight:
            if self.axes_txy is None:
                self.axes_txy=self.axes.twinx().twiny()
                self.__emitAxisChanged('Right')
                self.__emitAxisChanged('Top')
                self.axes_txy.minorticks_on()
            return self.axes_txy
    def Append(self,wave,axis=Axis.BottomLeft,id=None,appearance=None,offset=(0,0,0,0)):
        ax=self.__getAxes(axis)
        if isinstance(wave,Wave):
            wav=wave
        else:
            wav=Wave(wave)
        if appearance is None:
            self._Append(wav,ax,id,{},offset)
        else:
            self._Append(wav,ax,id,appearance,offset)
    def _Append(self,wav,ax,id,appearance,offset):
        if wav.data.ndim==1:
            self._Append1D(wav,ax,id,appearance,offset)
        if wav.data.ndim==2:
            self._Append2D(wav,ax,id,appearance,offset)
        self._emitDataChanged()
        self.draw()
    def _Append1D(self,wav,ax,ID,appearance,offset):
        if wav.x.ndim==0:
            xdata=np.arange(len(wav.data))
            ydata=wav.data
        else:
            xdata=wav.x
            ydata=wav.data
        xdata=xdata+offset[0]
        ydata=ydata+offset[1]
        if not offset[2]==0:
            xdata*=offset[2]
        if not offset[3]==0:
            ydata*=offset[3]
        line, = ax.plot(xdata,ydata,label=wav.Name())
        if ID is None:
            id=5000+len(self.getLines())
        else:
            id=ID
        line.set_zorder(id)
        self._Datalist.insert(id-5000,WaveData(wav,line,ax,id,appearance,offset))
    def _Append2D(self,wav,ax,ID,appearance,offset):
        if wav.x.ndim==0:
            xstart=0
            xend=len(wav.data)
        else:
            xstart=wav.x[0]
            xend=wav.x[len(wav.x)-1]
        if wav.y.ndim==0:
            ystart=0
            yend=len(wav.data[0])
        else:
            ystart=wav.y[0]
            yend=wav.y[len(wav.y)-1]
        xstart=xstart+offset[0]
        xend=xend+offset[0]
        ystart=ystart+offset[1]
        yend=yend+offset[1]
        if not offset[2]==0:
            xstart*=offset[2]
            xend*=offset[2]
        if not offset[3]==0:
            ystart*=offset[3]
            yend*=offset[3]
        im=ax.imshow(wav.data,aspect='auto',extent=(xstart,xend,ystart,yend))
        if ID is None:
            id=2000+len(self.getImages())
        else:
            id=ID
        im.set_zorder(id)
        self._Datalist.insert(id-2000,WaveData(wav,im,ax,id,appearance,offset))
    def Remove(self,indexes):
        for i in indexes:
            for d in self._Datalist:
                if i==d.id:
                    d.obj.remove()
                    self._Datalist.remove(d)
        self._emitDataChanged()
        self.draw()
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
            if d.wave.data.ndim==dim:
                res.append(d)
        return res
    def getLines(self):
        return self.getWaveData(1)
    def getImages(self):
        return self.getWaveData(2)
    def SaveAsDictionary(self,dictionary,path):
        i=0
        dic={}
        self.saveAppearance()
        for data in self._Datalist:
            dic[i]={}
            dic[i]['File']=os.path.relpath(data.wave.FileName(),path).replace('\\','/')
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
            i+=1
        dictionary['Datalist']=dic
    def LoadFromDictionary(self,dictionary,path):
        i=0
        sdir=pwd()
        cd(path)
        if 'Datalist' in dictionary:
            dic=dictionary['Datalist']
            while i in dic:
                p=dic[i]['File']
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
                else:
                    offset=(0,0,0,0)
                self.Append(p,axis,appearance=ap,offset=offset)
                i+=1
        self.loadAppearance()
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
                d.id=5000+n1
                n1+=1
            if d.wave.data.ndim==2:
                d.id=2000+n2
                n2+=1
            d.obj.set_zorder(d.id)
        self.draw()
    def saveAppearance(self):
        pass
    def loadAppearance(self):
        pass

class DataSelectableCanvas(FigureCanvasBase):
    def __init__(self,dpi):
        super().__init__(dpi)
        self.__indexes=[[],[],[],[]]
        self.__listener=[]
    def setSelectedIndexes(self,dim,indexes):
        self.__indexes[dim]=indexes
        self._emitDataSelected()
    def getSelectedIndexes(self,dim):
        return self.__indexes[dim]
    def getDataFromIndexes(self,dim,indexes):
        res=[]
        for i in indexes:
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

    def addDataSelectionListener(self,listener):
        self.__listener.append(weakref.ref(listener))
class DataSelectionBox(QTreeView):
    class _Model(QStandardItemModel):
        def __init__(self,parent,canvas):
            super().__init__(0,3)
            self.setHeaderData(0,Qt.Horizontal,'Line')
            self.setHeaderData(1,Qt.Horizontal,'Axis')
            self.setHeaderData(2,Qt.Horizontal,'Zorder')
            self.canvas=canvas
            self.parent=parent
        def clear(self):
            super().clear()
            self.setColumnCount(3)
            self.setHeaderData(0,Qt.Horizontal,'Line')
            self.setHeaderData(1,Qt.Horizontal,'Axis')
            self.setHeaderData(2,Qt.Horizontal,'Zorder')
        def supportedDropActions(self):
            return Qt.MoveAction
        def mimeData(self, indexes):
            mimedata = QMimeData()
            data=[]
            for i in indexes:
                if i.column() !=2:
                    continue
                t=eval(self.itemFromIndex(i).text())
                data.append(t)
            mimedata.setData('index',str(data).encode('utf-8'))
            mimedata.setText(str(data))
            return mimedata
        def mimeTypes(self):
            return ['index']
        def dropMimeData(self, data, action, row, column, parent):
            f=eval(data.text())
            par=self.itemFromIndex(parent)
            if par is None:
                if row==-1 and column==-1:
                    self.canvas.moveItem(f)
                else:
                    self.canvas.moveItem(f,self.item(row,2).text())
            else:
                self.canvas.moveItem(f,self.item(self.itemFromIndex(parent).row(),2).text())
            self.parent._loadstate()
            return False
    def __init__(self,canvas,dim):
        super().__init__()
        self.canvas=canvas
        self.__dim=dim
        canvas.addDataChangeListener(self)
        self.__initlayout()
        self._loadstate()
    def __initlayout(self):
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDropIndicatorShown(True)
        self.__model=DataSelectionBox._Model(self,self.canvas)
        self.setModel(self.__model)
        self.selectionModel().selectionChanged.connect(self.OnSelected)
    def _loadstate(self):
        list=self.canvas.getWaveData(self.__dim)
        self.__model.clear()
        i=1
        for l in list:
            self.__model.setItem(len(list)-i,0,QStandardItem(l.wave.Name()))
            self.__model.setItem(len(list)-i,1,QStandardItem(self.canvas.axesName(l.axis)))
            self.__model.setItem(len(list)-i,2,QStandardItem(str(l.id)))
            i+=1
    def OnSelected(self):
        indexes=self.selectedIndexes()
        ids=[]
        for i in indexes:
            if i.column()==2:
                ids.append(int(self.__model.itemFromIndex(i).text()))
        self.canvas.setSelectedIndexes(self.__dim,ids)
    def OnDataChanged(self):
        self._loadstate()
    def sizeHint(self):
        return QSize(150,100)

class DataHidableCanvas(DataSelectableCanvas):
    def __init__(self,dpi):
        super().__init__(dpi)
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
    def hide(self,dim,indexes):
        dat=self.getDataFromIndexes(dim,indexes)
        for d in dat:
            d.obj.set_visible(False)
        self.draw()
    def show(self,dim,indexes):
        dat=self.getDataFromIndexes(dim,indexes)
        for d in dat:
            d.obj.set_visible(True)
        self.draw()
class DataShowButton(QPushButton):
    def __init__(self,canvas,dim,flg):
        if flg:
            super().__init__('Show')
        else:
            super().__init__('Hide')
        self.__flg=flg
        self.canvas=canvas
        self.clicked.connect(self.__clicked)
        self.__dim=dim
    def __clicked(self):
        list=self.canvas.getSelectedIndexes(self.__dim)
        if self.__flg:
            self.canvas.show(self.__dim,list)
        else:
            self.canvas.hide(self.__dim,list)
class RightClickableSelectionBox(DataSelectionBox):
    def __init__(self,canvas,dim):
        super().__init__(canvas,dim)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
        self.canvas=canvas
        self.__dim=dim
    def buildContextMenu(self, qPoint):
        menu = QMenu(self)
        menulabels = ['Show', 'Hide', 'Remove', 'Display', 'Edit']
        actionlist = []
        for label in menulabels:
            actionlist.append(menu.addAction(label))
        action = menu.exec_(QCursor.pos())
        list=self.canvas.getSelectedIndexes(self.__dim)
        if action==None:
            return
        elif action.text() == 'Show':
            self.canvas.show(self.__dim,list)
        elif action.text() == 'Hide':
            self.canvas.hide(self.__dim,list)
        elif action.text() == 'Edit':
            print('Edit is not implemented yet.')
        elif action.text() == 'Display':
            g=Graph()
            data=self.canvas.getDataFromIndexes(self.__dim,list)
            for d in data:
                g.Append(d.wave)
        elif action.text() == 'Remove':
            self.canvas.Remove(list)

class OffsetAdjustableCanvas(DataHidableCanvas):
    def __init__(self,dpi):
        super().__init__(dpi)
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
class OffsetAdjustBox(QGroupBox):
    def __init__(self,canvas,dim):
        super().__init__("Offset")
        self.canvas=canvas
        canvas.addDataSelectionListener(self)
        self.__initlayout()
        self.__flg=False
        self.__dim=dim
    def __initlayout(self):
        gl=QGridLayout()
        self.__spin1=QDoubleSpinBox(valueChanged=self.__dataChanged)
        self.__spin2=QDoubleSpinBox(valueChanged=self.__dataChanged)
        self.__spin3=QDoubleSpinBox(valueChanged=self.__dataChanged)
        self.__spin4=QDoubleSpinBox(valueChanged=self.__dataChanged)
        gl.addWidget(QLabel('x offset'),0,0)
        gl.addWidget(self.__spin1,1,0)
        gl.addWidget(QLabel('x muloffset'),2,0)
        gl.addWidget(self.__spin3,3,0)
        gl.addWidget(QLabel('y offset'),0,1)
        gl.addWidget(self.__spin2,1,1)
        gl.addWidget(QLabel('y muloffset'),2,1)
        gl.addWidget(self.__spin4,3,1)
        self.setLayout(gl)
    def __dataChanged(self):
        if not self.__flg:
            indexes=self.canvas.getSelectedIndexes(self.__dim)
            self.canvas.setOffset((self.__spin1.value(),self.__spin2.value(),self.__spin3.value(),self.__spin4.value()),indexes)
    def OnDataSelected(self):
        self.__loadstate()
    def __loadstate(self):
        self.__flg=True
        indexes=self.canvas.getSelectedIndexes(self.__dim)
        if len(indexes)==0:
            return
        data=self.canvas.getOffset(indexes)[0]
        self.__spin1.setValue(data[0])
        self.__spin1.setRange(-10000000,10000000)
        self.__spin2.setValue(data[1])
        self.__spin2.setRange(-10000000,10000000)
        self.__spin3.setValue(data[2])
        self.__spin3.setRange(-10000000,10000000)
        self.__spin4.setValue(data[3])
        self.__spin4.setRange(-10000000,10000000)
        self.__flg=False
