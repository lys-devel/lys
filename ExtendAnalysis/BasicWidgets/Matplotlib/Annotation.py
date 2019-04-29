#!/usr/bin/env python
import random, weakref, gc, sys, os
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import colors, patches
from matplotlib.patches import BoxStyle
import matplotlib

from ExtendAnalysis import *
from .AreaSettings import *

class AnnotatableCanvas(AreaSettingCanvas, AnnotationHidableCanvasBase):
    def __init__(self,dpi):
        super().__init__(dpi)
        AnnotationHidableCanvasBase.__init__(self)
    def _addObject(self,obj):
        pass
    def _setZOrder(self,obj,ids):
        obj.set_zorder(ids)
    def _removeObject(self,obj):
        obj.remove()
    def _setVisible(self,obj,b):
        obj.set_visible(b)
    def _isVisible(self,obj):
        return obj.get_visible()

class TextAnnotationCanvas(AnnotatableCanvas, TextAnnotationCanvasBase):
    def __init__(self,dpi):
        super().__init__(dpi)
        TextAnnotationCanvasBase.__init__(self)
    def _makeObject(self,text,axis,appearance,id, x, y, box, size, picker):
        axes=self._getAxesFrom(axis)
        return axes.text(x,y,text,transform=axes.transAxes,picker=picker,bbox=box,size=size)
    def _setText(self,obj,txt):
        obj.set_text(txt)
    def _getText(self,obj):
        return obj.get_text()
    def _getAnnotAxis(self,obj):
        if obj.axes==self.axes:
            return Axis.BottomLeft
        if obj.axes==self.axes_ty:
            return Axis.TopLeft
        if obj.axes==self.axes_tx:
            return Axis.BottomRight
        if obj.axes==self.axes_txy:
            return Axis.TopRight
    def SaveAsDictionary(self,dictionary,path):
        AnnotatableCanvas.SaveAsDictionary(self,dictionary,path)
        TextAnnotationCanvasBase.SaveAsDictionary(self,dictionary,path)
    def LoadFromDictionary(self,dictionary,path):
        TextAnnotationCanvasBase.LoadFromDictionary(self,dictionary,path)
        super().LoadFromDictionary(dictionary,path)
class AnnotationEditableCanvas(TextAnnotationCanvas):
    def __init__(self,dpi):
        super().__init__(dpi)
        self.addFontChangeListener(self)
    def loadAnnotAppearance(self):
        super().loadAnnotAppearance()
        data=self.getAnnotations('text')
        for d in data:
            if 'Font' in d.appearance:
                self._setFont(d,FontInfo.FromDict(d.appearance['Font']))
    def OnFontChanged(self,name):
        super().OnFontChanged(name)
        list=self.getAnnotations('text')
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
    @saveCanvas
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
        data=self.getAnnotations('text')
        for d in data:
            t=d.obj.get_transform()
            if t==d.obj.axes.transData:
                d.appearance['PositionMode']='Relative'
            else:
                d.appearance['PositionMode']='Absolute'
            d.appearance['Position']=d.obj.get_position()
    def loadAnnotAppearance(self):
        super().loadAnnotAppearance()
        data=self.getAnnotations('text')
        for d in data:
            if 'PositionMode' in d.appearance:
                self.setAnnotPositionMode([d.id],d.appearance['PositionMode'])
                self.setAnnotPosition([d.id],d.appearance['Position'])
    @saveCanvas
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
    @saveCanvas
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
        data=self.getAnnotations('text')
        for d in data:
            d.appearance['BoxStyle']=self.getAnnotBoxStyle([d.id])[0]
            d.appearance['BoxFaceColor']=self.getAnnotBoxColor([d.id])[0]
            d.appearance['BoxEdgeColor']=self.getAnnotBoxEdgeColor([d.id])[0]
    def loadAnnotAppearance(self):
        super().loadAnnotAppearance()
        data=self.getAnnotations('text')
        for d in data:
            if 'BoxStyle' in d.appearance:
                self.setAnnotBoxStyle([d.id],d.appearance['BoxStyle'])
                self.setAnnotBoxColor([d.id],d.appearance['BoxFaceColor'])
                self.setAnnotBoxEdgeColor([d.id],d.appearance['BoxEdgeColor'])
    @saveCanvas
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
    @saveCanvas
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
    @saveCanvas
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
