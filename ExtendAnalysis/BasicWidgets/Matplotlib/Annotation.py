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
from .AreaSettings import *
from .CanvasBase import _saveCanvas

class AnnotationData(object):
    def __init__(self,name,obj,idn,appearance):
        self.name=name
        self.obj=obj
        self.id=idn
        self.appearance=appearance
        self.axes=self.obj.axes

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
    def hasAnnotType(self,type):
        return type in self._list
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
        return ids
    def loadAnnotAppearance(self):
        pass
    def saveAnnotAppearance(self):
        pass
    @_saveCanvas
    def clearAnnotations(self,type='text'):
        list=self.getAnnotations(type)
        ids=[]
        for l in list:
            ids.append(l.id)
        self.removeAnnotation(ids,type)
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

class TextAnnotationCanvas(AnnotationHidableCanvas):
    def __init__(self,dpi):
        super().__init__(dpi)
        self._registerType('text')
    @_saveCanvas
    def addText(self,text,axis=Axis.BottomLeft,appearance=None,id=None, x=0.5, y=0.5, box=dict(boxstyle='round', fc='w'), size=10, picker=True):
        axes=self._getAxesFrom(axis)
        a=axes.text(x,y,text,transform=axes.transAxes,picker=picker,bbox=box,size=size)
        return self.addAnnotation('text',text,a,appearance,id)
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

class AnnotationSettingCanvas(AnnotationBoxAdjustableCanvas):
    pass
