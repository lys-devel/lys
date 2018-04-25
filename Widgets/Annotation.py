#!/usr/bin/env python
import random, weakref, gc, sys, os
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure, SubplotParams
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import colors, patches
from matplotlib.patches import BoxStyle
import matplotlib

from ExtendAnalysis.ExtendType import *
from ExtendAnalysis import *
from ExtendAnalysis.GraphWindow import *
from .ColorWidgets import *
from .AreaSettings import *
from .CanvasBase import _saveCanvas

class AnnotationData(object):
    def __init__(self,name,obj,idn,appearance):
        self.name=name
        self.obj=obj
        self.id=idn
        self.appearance=appearance

class AnnotatableCanvas(AreaSettingCanvas):
    def __init__(self,dpi):
        super().__init__(dpi)
        self._list={}
        self._sel={}
        self._changed={}
        self._edited={}
        self._selected={}
        self._id_start={}
        self._id_seed=10000
    def _registerType(self,type):
        self._list[type]=[]
        self._sel[type]=[]
        self._changed[type]=[]
        self._edited[type]=[]
        self._selected[type]=[]
        self._id_start[type]=self._id_seed
        self._id_seed+=300
    @_saveCanvas
    def addAnnotation(self,type,name,obj,appearance=None,id=None):
        if id is None:
            ids=self._id_start[type]+len(self._list[type])
        else:
            ids=id
        obj.set_zorder(ids)
        if appearance is None:
            self._list[type].insert(ids-self._id_start[type],AnnotationData(name,obj,ids,{}))
        else:
            self._list[type].insert(ids-self._id_start[type],AnnotationData(name,obj,ids,appearance))
        self._emitAnnotationChanged(type)
        self.draw()
    def loadAnnotAppearance(self):
        pass
    def saveAnnotAppearance(self):
        pass
    @_saveCanvas
    def removeAnnotation(self,indexes,type='text'):
        for i in indexes:
            for d in self._list[type]:
                if i==d.id:
                    d.obj.remove()
                    self._list[type].remove(d)
        self._reorderAnnotation(type)
        self._emitAnnotationChanged(type)
        self.draw()
    def getAnnotations(self,type='text'):
        return self._list[type]
    def getSelectedAnnotations(self,type='text'):
        return self._sel[type]
    def setSelectedAnnotations(self,indexes,type='text'):
        if hasattr(indexes, '__iter__'):
            self._sel[type]=indexes
        else:
            self._sel[type]=[indexes]
        self._emitAnnotationSelected()
    def getAnnotationFromIndexes(self,indexes,type='text'):
        res=[]
        if hasattr(indexes, '__iter__'):
            list=indexes
        else:
            list=[indexes]
        for i in list:
            for d in self._list[type]:
                if d.id==i:
                    res.append(d)
        return res
    def _reorderAnnotation(self,type='text'):
        n=0
        for d in self._list[type]:
            d.obj.set_zorder(10000+n)
            d.id=10000+n
            n+=1
        self.draw()
    def _findIndex(self,id,type='text'):
        res=-1
        for d in self._list[type]:
            if d.obj.get_zorder()==id:
                res=self._list[type].index(d)
        return res
    @_saveCanvas
    def moveAnnotation(self,list,target=None,type='text'):
        tar=eval(str(target))
        for l in list:
            n=self._findIndex(l)
            item_n=self._list[type][n]
            self._list[type].remove(item_n)
            if tar is not None:
                self._list[type].insert(self._findIndex(tar)+1,item_n)
            else:
                self._list[type].insert(0,item_n)
        self._reorderAnnotation()

    def addAnnotationChangeListener(self,listener,type='text'):
        self._changed[type].append(weakref.ref(listener))
    def addAnnotationSelectedListener(self,listener,type='text'):
        self._selected[type].append(weakref.ref(listener))
    def addAnnotationEditedListener(self,listener,type='text'):
        self._edited[type].append(weakref.ref(listener))
    def _emitAnnotationChanged(self,type='text'):
        for l in self._changed[type]:
            if l() is None:
                self._changed[type].remove(l)
            else:
                l().OnAnnotationChanged()
    def _emitAnnotationSelected(self,type='text'):
        for l in self._selected[type]:
            if l() is None:
                self._selected[type].remove(l)
            else:
                l().OnAnnotationSelected()
    def _emitAnnotationEdited(self,type='text'):
        for l in self._edited[type]:
            if l() is None:
                self._edited[type].remove(l)
            else:
                l().OnAnnotationEdited()

class AnnotationHidableCanvas(AnnotatableCanvas):
    def saveAnnotAppearance(self):
        super().saveAnnotAppearance()
        data=self.getAnnotations()
        for d in data:
            d.appearance['Visible']=d.obj.get_visible()
    def loadAnnotAppearance(self):
        super().loadAnnotAppearance()
        data=self.getAnnotations()
        for d in data:
            if 'Visible' in d.appearance:
                d.obj.set_visible(d.appearance['Visible'])
    @_saveCanvas
    def hideAnnotation(self,indexes,type='text'):
        dat=self.getAnnotationFromIndexes(indexes,type=type)
        for d in dat:
            d.obj.set_visible(False)
        self.draw()
    @_saveCanvas
    def showAnnotation(self,indexes,type='text'):
        dat=self.getAnnotationFromIndexes(indexes,type=type)
        for d in dat:
            d.obj.set_visible(True)
        self.draw()
class AnnotationSelectionBox(QTreeView):
    class _Model(QStandardItemModel):
        def __init__(self,canvas,type='text'):
            super().__init__(0,3)
            self.setHeaderData(0,Qt.Horizontal,'Line')
            self.setHeaderData(1,Qt.Horizontal,'Axis')
            self.setHeaderData(2,Qt.Horizontal,'Zorder')
            self.canvas=canvas
            self.type=type
        def clear(self):
            super().clear()
            self.setColumnCount(3)
            self.setHeaderData(0,Qt.Horizontal,'Annotation')
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
                    self.canvas.moveAnnotation(f,type=self.type)
                else:
                    self.canvas.moveAnnotation(f,self.item(row,2).text(),type=self.type)
            else:
                self.canvas.moveAnnotation(f,self.item(self.itemFromIndex(parent).row(),2).text(),type=self.type)
            self.canvas._emitAnnotationChanged()
            return False
    def __init__(self,canvas,type='text'):
        super().__init__()
        self.canvas=canvas
        self.__type=type
        self.__initlayout()
        self._loadstate()
        self.canvas.addAnnotationChangeListener(self,type)
        self.canvas.addAnnotationEditedListener(self,type)
        self.canvas.addAnnotationSelectedListener(self,type)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
        self.flg=False
    def __initlayout(self):
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDropIndicatorShown(True)
        self.__model=AnnotationSelectionBox._Model(self.canvas,self.__type)
        self.setModel(self.__model)
        self.selectionModel().selectionChanged.connect(self.OnSelected)
    def OnAnnotationSelected(self):
        if self.flg:
            return
        self.flg=True
        indexes=self.canvas.getSelectedAnnotations(self.__type)
        list=self.canvas.getAnnotations(self.__type)
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
        self.flg=False
    def _loadstate(self):
        list=self.canvas.getAnnotations(self.__type)
        self.__model.clear()
        i=1
        for l in list:
            self.__model.setItem(len(list)-i,0,QStandardItem(l.name))
            self.__model.setItem(len(list)-i,1,QStandardItem(self.canvas.axesName(l.obj.axes)))
            self.__model.setItem(len(list)-i,2,QStandardItem(str(l.id)))
            i+=1

    def OnSelected(self):
        if self.flg:
            return
        self.flg=True
        indexes=self.selectedIndexes()
        ids=[]
        for i in indexes:
            if i.column()==2:
                ids.append(int(self.__model.itemFromIndex(i).text()))
        self.canvas.setSelectedAnnotations(ids,self.__type)
        self.flg=False
    def OnAnnotationChanged(self):
        self._loadstate()
    def OnAnnotationEdited(self):
        list=self.canvas.getAnnotations(self.__type)
        i=1
        for l in list:
            self.__model.itemFromIndex(self.__model.index(len(list)-i,0)).setText(l.name)
            i+=1
    def sizeHint(self):
        return QSize(150,100)
    def buildContextMenu(self, qPoint):
        menu = QMenu(self)
        menulabels = ['Show', 'Hide', 'Add', 'Remove']
        actionlist = []
        for label in menulabels:
            actionlist.append(menu.addAction(label))
        action = menu.exec_(QCursor.pos())
        list=self.canvas.getSelectedAnnotations(self.__type)
        if action==None:
            return
        elif action.text() == 'Show':
            self.canvas.showAnnotation(list,self.__type)
        elif action.text() == 'Hide':
            self.canvas.hideAnnotation(list,self.__type)
        elif action.text() == 'Remove':
            self.canvas.removeAnnotation(list,self.__type)
        elif action.text() == 'Add':
            self.canvas.addText("")

class TextAnnotationCanvas(AnnotationHidableCanvas):
    def __init__(self,dpi):
        super().__init__(dpi)
        self._registerType('text')
    @_saveCanvas
    def addText(self,text,axis=Axis.BottomLeft,appearance=None,id=None):
        axes=self._getAxesFrom(axis)
        a=axes.text(0.5,0.5,text,transform=axes.transAxes,picker=True)
        self.addAnnotation('text',text,a,appearance,id)
    @_saveCanvas
    def setAnnotationText(self,indexes,txt):
        list=self.getAnnotationFromIndexes(indexes)
        for l in list:
            l.obj.set_text(txt)
        self._emitAnnotationEdited()
        self.draw()
    def getAnnotationText(self,indexes):
        res=[]
        list=self.getAnnotationFromIndexes(indexes)
        for l in list:
            res.append(l.obj.get_text())
        return res

    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        i=0
        dic={}
        self.saveAnnotAppearance()
        for data in self._list['text']:
            dic[i]={}
            dic[i]['Text']=data.obj.get_text()
            dic[i]['Appearance']=str(data.appearance)
            if data.obj.axes==self.axes:
                axis=1
            if data.obj.axes==self.axes_ty:
                axis=2
            if data.obj.axes==self.axes_tx:
                axis=3
            if data.obj.axes==self.axes_txy:
                axis=4
            dic[i]['Axis']=axis
            i+=1
        dictionary['Textlist']=dic
    def LoadFromDictionary(self,dictionary,path):
        if 'Textlist' in dictionary:
            dic=dictionary['Textlist']
            i=0
            while i in dic:
                t=dic[i]['Text']
                appearance=eval(dic[i]['Appearance'])
                axis=dic[i]['Axis']
                if axis==1:
                    axis=Axis.BottomLeft
                if axis==2:
                    axis=Axis.TopLeft
                if axis==3:
                    axis=Axis.BottomRight
                if axis==4:
                    axis=Axis.TopRight
                self.addText(t,axis,appearance=appearance)
                i+=1
        super().LoadFromDictionary(dictionary,path)
class AnnotationEditableCanvas(TextAnnotationCanvas):
    def __init__(self,dpi):
        super().__init__(dpi)
        self.addFontChangeListener(self)
    def loadAnnotAppearance(self):
        super().loadAnnotAppearance()
        data=self.getAnnotations()
        for d in data:
            if 'Font' in d.appearance:
                self._setFont(d,FontInfo.FromDict(d.appearance['Font']))
    def OnFontChanged(self,name):
        super().OnFontChanged(name)
        list=self.getAnnotations()
        for l in list:
            if 'Font_def' in l.appearance:
                if l.appearance['Font_def'] is not None and name in [l.appearance['Font_def'],'Default']:
                    f=self.getFont(name)
                    l.obj.set_family(f.family)
                    l.obj.set_size(f.size)
                    l.obj.set_color(f.color)
        self.draw()
    def _setFont(self,annot,font):
        if not isinstance(font,FontInfo):
            f=self.getFont(font)
        else:
            f=font
        annot.obj.set_family(f.family)
        annot.obj.set_size(f.size)
        annot.obj.set_color(f.color)
        annot.appearance['Font']=f.ToDict()
    @_saveCanvas
    def setAnnotationFont(self,indexes,font='Default',default=False):
        list=self.getAnnotationFromIndexes(indexes)
        for l in list:
            self._setFont(l,font)
            if default and not isinstance(font,FontInfo):
                l.appearance['Font_def']=font
            else:
                l.appearance['Font_def']=None
        self.draw()
    def getAnnotationFontDefault(self,indexes):
        res=[]
        list=self.getAnnotationFromIndexes(indexes)
        for l in list:
            if 'Font_def' in l.appearance:
                if l.appearance['Font_def'] is not None:
                    res.append(True)
                else:
                    res.append(False)
            else:
                res.append(False)
        return res
    def getAnnotationFont(self,indexes):
        res=[]
        list=self.getAnnotationFromIndexes(indexes)
        for l in list:
            res.append(FontInfo(l.obj.get_family()[0],l.obj.get_size(),l.obj.get_color()))
        return res
class AnnotationEditBox(QWidget):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        self.__flg=False
        self.__initlayout()
        self.canvas.addAnnotationSelectedListener(self)
    def __initlayout(self):
        l=QVBoxLayout()
        self.__font=FontSelectWidget(self.canvas)
        self.__font.fontChanged.connect(self.__fontChanged)
        l.addWidget(self.__font)
        self.__txt=QTextEdit()
        self.__txt.textChanged.connect(self.__txtChanged)
        self.__txt.setMinimumHeight(10)
        self.__txt.setMaximumHeight(50)
        l.addWidget(self.__txt)
        self.setLayout(l)
    def __loadstate(self):
        self.__flg=True
        indexes=self.canvas.getSelectedAnnotations()
        if not len(indexes)==0:
            tmp=self.canvas.getAnnotationText(indexes)[0]
            self.__txt.setText(tmp)
            tmp=self.canvas.getAnnotationFontDefault(indexes)[0]
            self.__font.setFontDefault(tmp)
            tmp=self.canvas.getAnnotationFont(indexes)[0]
            self.__font.setFont(tmp)
        self.__flg=False
    def __txtChanged(self):
        if self.__flg:
            return
        txt=self.__txt.toPlainText()
        indexes=self.canvas.getSelectedAnnotations()
        self.canvas.setAnnotationText(indexes,txt)
    def __fontChanged(self):
        if self.__flg:
            return
        indexes=self.canvas.getSelectedAnnotations()
        if self.__font.getFontDefault():
            self.canvas.setAnnotationFont(indexes,font='Text',default=True)
        else:
            self.canvas.setAnnotationFont(indexes,self.__font.getFont())
    def OnAnnotationSelected(self):
        self.__loadstate()

class AnnotationMovableCanvas(AnnotationEditableCanvas):
    def saveAnnotAppearance(self):
        super().saveAnnotAppearance()
        data=self.getAnnotations()
        for d in data:
            t=d.obj.get_transform()
            if t==d.obj.axes.transData:
                d.appearance['PositionMode']='Relative'
            else:
                d.appearance['PositionMode']='Absolute'
            d.appearance['Position']=d.obj.get_position()
    def loadAnnotAppearance(self):
        super().loadAnnotAppearance()
        data=self.getAnnotations()
        for d in data:
            if 'PositionMode' in d.appearance:
                self.setAnnotPositionMode([d.id],d.appearance['PositionMode'])
                self.setAnnotPosition([d.id],d.appearance['Position'])
    @_saveCanvas
    def setAnnotPosition(self,indexes,xy):
        list=self.getAnnotationFromIndexes(indexes)
        for l in list:
            l.obj.set_position(xy)
        self._emitAnnotationSelected()
        self.draw()
    def getAnnotPosition(self,indexes):
        res=[]
        list=self.getAnnotationFromIndexes(indexes)
        for l in list:
            res.append(l.obj.get_position())
        return res
    @_saveCanvas
    def setAnnotPositionMode(self,indexes,mode):
        list=self.getAnnotationFromIndexes(indexes)
        for l in list:
            old_p=l.obj.get_position()
            old_t=l.obj.get_transform()
            ax=l.obj.axes
            ylim=ax.get_ylim()
            xlim=ax.get_xlim()
            if mode=='Absolute':
                l.obj.set_transform(self.axes.transAxes)
                if old_t==self.axes.transData:
                    l.obj.set_position(((old_p[0]-xlim[0])/(xlim[1]-xlim[0]),(old_p[1]-ylim[0])/(ylim[1]-ylim[0])))
            elif mode=='Relative':
                l.obj.set_transform(self.axes.transData)
                if old_t==self.axes.transAxes:
                    l.obj.set_position((xlim[0]+old_p[0]*(xlim[1]-xlim[0]),ylim[0]+old_p[1]*(ylim[1]-ylim[0])))
        self.draw()
    def getAnnotPositionMode(self,indexes):
        res=[]
        list=self.getAnnotationFromIndexes(indexes)
        for l in list:
            t=l.obj.get_transform()
            if t==self.axes.transAxes:
                res.append('Absolute')
            else:
                res.append('Relative')
        return res
class AnnotationMoveBox(QWidget):
    def __init__(self,canvas):
        super().__init__()
        self.__initlayout()
        self.canvas=canvas
        self.canvas.addAnnotationSelectedListener(self)
    def __initlayout(self):
        l=QVBoxLayout()
        self.__mode=QComboBox()
        self.__mode.addItems(['Absolute','Relative'])
        self.__mode.activated.connect(self.__chgMod)
        l.addWidget(self.__mode)
        gl=QGridLayout()
        self.__x=QDoubleSpinBox()
        self.__y=QDoubleSpinBox()
        self.__x.setRange(-float('inf'),float('inf'))
        self.__y.setRange(-float('inf'),float('inf'))
        self.__x.setDecimals(5)
        self.__y.setDecimals(5)
        self.__x.valueChanged.connect(self.__changePos)
        self.__y.valueChanged.connect(self.__changePos)
        gl.addWidget(QLabel('x'),0,0)
        gl.addWidget(QLabel('y'),0,1)
        gl.addWidget(self.__x,1,0)
        gl.addWidget(self.__y,1,1)
        l.addLayout(gl)
        self.setLayout(l)
    def OnAnnotationSelected(self):
        self.__loadstate()
    def __loadstate(self):
        list=self.canvas.getSelectedAnnotations()
        if len(list)==0:
            return
        tmp=self.canvas.getAnnotPositionMode(list)[0]
        self.__mode.setCurrentIndex(['Absolute','Relative'].index(tmp))
        tmp=self.canvas.getAnnotPosition(list)[0]
        self.__x.setValue(tmp[0])
        self.__y.setValue(tmp[1])
    def __chgMod(self):
        indexes=self.canvas.getSelectedAnnotations()
        self.canvas.setAnnotPositionMode(indexes,self.__mode.currentText())
        self.__loadstate()
    def __changePos(self):
        indexes=self.canvas.getSelectedAnnotations()
        self.canvas.setAnnotPosition(indexes,(self.__x.value(),self.__y.value()))

class AnnotationBoxAdjustableCanvas(AnnotationMovableCanvas):
    def saveAnnotAppearance(self):
        super().saveAnnotAppearance()
        data=self.getAnnotations()
        for d in data:
            d.appearance['BoxStyle']=self.getAnnotBoxStyle([d.id])[0]
            d.appearance['BoxFaceColor']=self.getAnnotBoxColor([d.id])[0]
            d.appearance['BoxEdgeColor']=self.getAnnotBoxEdgeColor([d.id])[0]
    def loadAnnotAppearance(self):
        super().loadAnnotAppearance()
        data=self.getAnnotations()
        for d in data:
            if 'BoxStyle' in d.appearance:
                self.setAnnotBoxStyle([d.id],d.appearance['BoxStyle'])
                self.setAnnotBoxColor([d.id],d.appearance['BoxFaceColor'])
                self.setAnnotBoxEdgeColor([d.id],d.appearance['BoxEdgeColor'])
    @_saveCanvas
    def setAnnotBoxStyle(self,indexes,style):
        list=self.getAnnotationFromIndexes(indexes)
        for l in list:
            box=l.obj.get_bbox_patch()
            if style=='none':
                if box is not None:
                    box.set_visible(False)
            else:
                l.obj.set_bbox(dict(boxstyle=style))
                self.setAnnotBoxColor([l.id],'w')
                self.setAnnotBoxEdgeColor([l.id],'k')
        self.draw()
    def _checkBoxStyle(self,box):
        if isinstance(box,BoxStyle.Square):
            return 'square'
        elif isinstance(box,BoxStyle.Circle):
            return 'circle'
        elif isinstance(box,BoxStyle.DArrow):
            return 'darrow'
        elif isinstance(box,BoxStyle.RArrow):
            return 'rarrow'
        elif isinstance(box,BoxStyle.LArrow):
            return 'larrow'
        elif isinstance(box,BoxStyle.Round):
            return 'round'
        elif isinstance(box,BoxStyle.Round4):
            return 'round4'
        elif isinstance(box,BoxStyle.Roundtooth):
            return 'roundtooth'
        elif isinstance(box,BoxStyle.Sawtooth):
            return 'sawtooth'
        return 'none'
    def getAnnotBoxStyle(self,indexes):
        res=[]
        list=self.getAnnotationFromIndexes(indexes)
        for l in list:
            box=l.obj.get_bbox_patch()
            if box is None:
                res.append('none')
                continue
            if not box.get_visible():
                res.append('none')
                continue
            else:
                res.append(self._checkBoxStyle(box.get_boxstyle()))
                continue
        return res
    @_saveCanvas
    def setAnnotBoxColor(self,indexes,color):
        list=self.getAnnotationFromIndexes(indexes)
        for l in list:
            box=l.obj.get_bbox_patch()
            if box is not None:
                box.set_facecolor(color)
        self.draw()
    def getAnnotBoxColor(self,indexes):
        res=[]
        list=self.getAnnotationFromIndexes(indexes)
        for l in list:
            box=l.obj.get_bbox_patch()
            if box is None:
                res.append('w')
            else:
                res.append(box.get_facecolor())
        return res
    @_saveCanvas
    def setAnnotBoxEdgeColor(self,indexes,color):
        list=self.getAnnotationFromIndexes(indexes)
        for l in list:
            box=l.obj.get_bbox_patch()
            if box is not None:
                box.set_edgecolor(color)
        self.draw()
    def getAnnotBoxEdgeColor(self,indexes):
        res=[]
        list=self.getAnnotationFromIndexes(indexes)
        for l in list:
            box=l.obj.get_bbox_patch()
            if box is None:
                res.append('k')
            else:
                res.append(box.get_edgecolor())
        return res
class AnnotationBoxAdjustBox(QWidget):
    list=['none','square','circle','round','round4','larrow','rarrow','darrow','roundtooth','sawtooth']
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        self.__initlayout()
        self.__flg=False
        self.canvas.addAnnotationSelectedListener(self)
    def __initlayout(self):
        gl=QGridLayout()
        gl.addWidget(QLabel('Mode'),0,0)
        self.__mode=QComboBox()
        self.__mode.addItems(self.list)
        self.__mode.activated.connect(self.__modeChanged)
        gl.addWidget(self.__mode,0,1)

        gl.addWidget(QLabel('Face Color'),1,0)
        self.__fc=ColorSelection()
        self.__fc.colorChanged.connect(self.__fcChanged)
        gl.addWidget(self.__fc,1,1)

        gl.addWidget(QLabel('Edge Color'),2,0)
        self.__ec=ColorSelection()
        self.__ec.colorChanged.connect(self.__ecChanged)
        gl.addWidget(self.__ec,2,1)

        self.setLayout(gl)
    def OnAnnotationSelected(self):
        self.__loadstate()
    def __loadstate(self):
        self.__flg=True
        indexes=self.canvas.getSelectedAnnotations()
        if not len(indexes)==0:
            tmp=self.canvas.getAnnotBoxStyle(indexes)[0]
            self.__mode.setCurrentIndex(self.list.index(tmp))
            tmp=self.canvas.getAnnotBoxColor(indexes)[0]
            self.__fc.setColor(tmp)
            tmp=self.canvas.getAnnotBoxEdgeColor(indexes)[0]
            self.__ec.setColor(tmp)
        self.__flg=False
    def __modeChanged(self):
        if self.__flg:
            return
        indexes=self.canvas.getSelectedAnnotations()
        self.canvas.setAnnotBoxStyle(indexes,self.__mode.currentText())
        self.__loadstate()
    def __fcChanged(self):
        if self.__flg:
            return
        indexes=self.canvas.getSelectedAnnotations()
        self.canvas.setAnnotBoxColor(indexes,self.__fc.getColor())
    def __ecChanged(self):
        if self.__flg:
            return
        indexes=self.canvas.getSelectedAnnotations()
        self.canvas.setAnnotBoxEdgeColor(indexes,self.__ec.getColor())
class AnnotationBox(QWidget):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        layout=QVBoxLayout()
        layout.addWidget(AnnotationSelectionBox(canvas))
        tab=QTabWidget()
        tab.addTab(AnnotationEditBox(canvas),'Text')
        tab.addTab(AnnotationMoveBox(canvas),'Position')
        tab.addTab(AnnotationBoxAdjustBox(canvas),'Box')
        layout.addWidget(tab)
        self.setLayout(layout)

class AnnotationSettingCanvas(AnnotationBoxAdjustableCanvas):
    pass
