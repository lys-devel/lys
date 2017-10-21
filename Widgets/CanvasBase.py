#!/usr/bin/env python
import weakref, sys, os
from enum import Enum
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure, SubplotParams
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ExtendAnalysis import *

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
class FigureCanvasBase(FigureCanvas):
    def __init__(self, dpi=100):
        self.fig=Figure(dpi=dpi)
        super().__init__(self.fig)
        self.axes = self.fig.add_subplot(111)#TODO #This line takes 0.3s for each image.
        self.axes.minorticks_on()
        self.axes.xaxis.set_picker(15)
        self.axes.yaxis.set_picker(15)
        self.axes_tx=None
        self.axes_ty=None
        self.axes_txy=None
        self._Datalist=[]
        self.__listener=[]
        self.__lisaxis=[]
        self.__lisdraw=[]
        self.drawflg=False

        Wave.AddWaveModificationListener(self)

    def OnWaveModified(self,wave):
        flg=False
        self.saveAppearance()
        for d in self._Datalist:
            if wave==d.wave:
                d.obj.remove()
                self._Datalist.remove(d)
                self._Append(wave,d.axis,d.id,appearance=d.appearance,offset=d.offset,zindex=d.zindex)
                flg=True
        self.loadAppearance()
        if(flg):
            self.draw()
    def IsDrawEnabled(self):
        return self.drawflg
    def EnableDraw(self,b):
        self.drawflg=b
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
    def Append(self,wave,axis=Axis.BottomLeft,id=None,appearance=None,offset=(0,0,0,0),zindex=0):
        ax=self.__getAxes(axis)
        if isinstance(wave,Wave):
            wav=wave
        else:
            wav=Wave(wave)
        if appearance is None:
            return self._Append(wav,ax,id,{},offset,zindex)
        else:
            return self._Append(wav,ax,id,appearance,offset,zindex)
    def _Append(self,wav,ax,id,appearance,offset,zindex=0):
        if wav.data.ndim==1:
            id=self._Append1D(wav,ax,id,appearance,offset)
        if wav.data.ndim==2:
            id=self._Append2D(wav,ax,id,appearance,offset)
        if wav.data.ndim==3:
            id=self._Append3D(wav,ax,id,appearance,offset,zindex)
        self._emitDataChanged()
        self.draw()
        return id
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
        line, = ax.plot(xdata,ydata,label=wav.Name(),picker=5)
        if ID is None:
            id=-2000+len(self.getLines())
        else:
            id=ID
        line.set_zorder(id)
        self._Datalist.insert(id+2000,WaveData(wav,line,ax,id,appearance,offset))
        return id
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
        im=ax.imshow(wav.data,aspect='auto',extent=(xstart,xend,ystart,yend),picker=True)
        if ID is None:
            id=-5000+len(self.getImages())
        else:
            id=ID
        im.set_zorder(id)
        self._Datalist.insert(id+5000,WaveData(wav,im,ax,id,appearance,offset))
        return id
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
        return id

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
            dic[i]['ZIndex']=str(data.zindex)
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
                if 'ZIndex' in dic[i]:
                    zi=eval(dic[i]['ZIndex'])
                else:
                    offset=(0,0,0,0)
                self.Append(p,axis,appearance=ap,offset=offset,zindex=zi)
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
class DataSelectionBox(QTreeView):
    class _Model(QStandardItemModel):
        def __init__(self,canvas):
            super().__init__(0,3)
            self.setHeaderData(0,Qt.Horizontal,'Line')
            self.setHeaderData(1,Qt.Horizontal,'Axis')
            self.setHeaderData(2,Qt.Horizontal,'Zorder')
            self.canvas=canvas
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
            return False
    def __init__(self,canvas,dim):
        super().__init__()
        self.canvas=canvas
        self.__dim=dim
        self.__initlayout()
        self.flg=False
        self._loadstate()
        canvas.addDataChangeListener(self)
        canvas.addDataSelectionListener(self)
    def __initlayout(self):
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDropIndicatorShown(True)
        self.__model=DataSelectionBox._Model(self.canvas)
        self.setModel(self.__model)
        self.selectionModel().selectionChanged.connect(self.OnSelected)
    def OnDataSelected(self):
        if self.flg:
            return
        indexes=self.canvas.getSelectedIndexes(self.__dim)
        list=self.canvas.getWaveData(self.__dim)
        selm=self.selectionModel()
        for i in range(len(list)):
            index0=self.__model.index(len(list)-i-1,0)
            index1=self.__model.index(len(list)-i-1,1)
            index2=self.__model.index(len(list)-i-1,2)
            id=float(self.__model.itemFromIndex(index2).text())
            if id in indexes:
                selm.select(index0,QItemSelectionModel.Select)
                selm.select(index1,QItemSelectionModel.Select)
                selm.select(index2,QItemSelectionModel.Select)
            else:
                selm.select(index0,QItemSelectionModel.Deselect)
                selm.select(index1,QItemSelectionModel.Deselect)
                selm.select(index2,QItemSelectionModel.Deselect)

    def _loadstate(self):
        list=self.canvas.getWaveData(self.__dim)
        self.__model.clear()
        i=1
        for l in list:
            self.__model.setItem(len(list)-i,0,QStandardItem(l.wave.Name()))
            self.__model.setItem(len(list)-i,1,QStandardItem(self.canvas.axesName(l.axis)))
            self.__model.setItem(len(list)-i,2,QStandardItem(str(l.id)))
            i+=1
        self.OnDataSelected()
    def OnSelected(self):
        self.flg=True
        indexes=self.selectedIndexes()
        ids=[]
        for i in indexes:
            if i.column()==2:
                ids.append(int(self.__model.itemFromIndex(i).text()))
        self.canvas.setSelectedIndexes(self.__dim,ids)
        self.flg=False
    def OnDataChanged(self):
        self._loadstate()
    def sizeHint(self):
        return QSize(150,100)

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
    def hideData(self,dim,indexes):
        dat=self.getDataFromIndexes(dim,indexes)
        for d in dat:
            d.obj.set_visible(False)
        self.draw()
    def showData(self,dim,indexes):
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
            self.canvas.showData(self.__dim,list)
        else:
            self.canvas.hideData(self.__dim,list)
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
            self.canvas.showData(self.__dim,list)
        elif action.text() == 'Hide':
            self.canvas.hideData(self.__dim,list)
        elif action.text() == 'Edit':
            print('Edit is not implemented yet.')
        elif action.text() == 'Display':
            from ExtendAnalysis.GraphWindow import Graph
            g=Graph()
            data=self.canvas.getDataFromIndexes(self.__dim,list)
            for d in data:
                g.Append(d.wave)
        elif action.text() == 'Remove':
            self.canvas.Remove(list)

class OffsetAdjustableCanvas(DataHidableCanvas):
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
