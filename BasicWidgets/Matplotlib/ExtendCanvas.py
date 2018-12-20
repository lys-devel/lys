#!/usr/bin/env python
import random, sys, os
from enum import Enum
from PyQt5.QtGui import *

from .SaveSettings import *
from .CanvasBase import _saveCanvas

class ExtendCanvas(SaveSettingCanvas):
    keyPressed=pyqtSignal(QKeyEvent)
    savedDict={}
    def __init__(self, dpi=100):
        self.saveflg=False
        self.EnableDraw(False)
        super().__init__(dpi=dpi)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
        self.modf=weakref.WeakMethod(self.defModFunc)
        self.moveText=False
        self.textPosStart=None
        self.cursorPosStart=None
        self.EnableDraw(True)
    def __findAxis(self,axis):
        axes=axis.axes
        xy=isinstance(axis,XAxis)
        if axes==self.axes:
            if xy:
                return 'Bottom'
            else:
                return 'Left'
        elif axes==self.axes_ty:
            if xy:
                return 'Top'
            else:
                return 'Left'
        elif axes==self.axes_tx:
            if xy:
                return 'Bottom'
            else:
                return 'Right'
        elif axes==self.axes_txy:
            if xy:
                return 'Top'
            else:
                return 'Right'
    def __GlobalToAxis(self, x, y, ax):
        loc=self.__GlobalToRatio(x,y,ax)
        xlim=ax.get_xlim()
        ylim=ax.get_ylim()
        x_ax=xlim[0]+(xlim[1]-xlim[0])*loc[0]
        y_ax=ylim[0]+(ylim[1]-ylim[0])*loc[1]
        return [x_ax,y_ax]
    def __GlobalToRatio(self, x, y, ax):
        ran=ax.get_position()
        x_loc=(x - ran.x0 * self.width())/((ran.x1 - ran.x0)*self.width())
        y_loc=(y - ran.y0 * self.height())/((ran.y1 - ran.y0)*self.height())
        return [x_loc,y_loc]
    def OnMouseUp(self, event):
        if self.moveText == True and event.button == 1:
            self.moveText=False
        return super().OnMouseUp(event)
    def OnMouseMove(self, event):
        if self.moveText == True:
            mode=self.getAnnotPositionMode(self.annotindex)[0]
            if mode == 'Absolute':
                d=self.__GlobalToRatio(event.x,event.y,self.axes)
            elif mode=='Relative':
                d=self.__GlobalToAxis(event.x,event.y,self.axes)
            self.setAnnotPosition(self.annotindex,(self.textPosStart[0]+d[0]-self.cursorPosStart[0],self.textPosStart[1]+d[1]-self.cursorPosStart[1]))
            self.draw()
        else:
            return super().OnMouseMove(event)
    def OnMouseDown(self, event):
        if event.dblclick:
            self.annot=self.getPickedAnnotation()
            if self.annot is not None:
                self.modf()(self,'Annot.')
                self.setSelectedAnnotations(self.annot.get_zorder())
                return super().OnMouseDown(event)
            axis=self.getPickedAxis()
            if axis is not None:
                self.modf()(self,'Axis')
                self.setSelectedAxis(self.__findAxis(axis))
                return super().OnMouseDown(event)
            line=self.getPickedLine()
            if line is not None:
                self.modf()(self,'Lines')
                w=self.getWaveDataFromArtist(line)
                self.setSelectedIndexes(1,w.id)
                return super().OnMouseDown(event)
            image=self.getPickedImage()
            if image is not None:
                self.modf()(self,'Images')
                w=self.getWaveDataFromArtist(image)
                self.setSelectedIndexes(2,w.id)
                return super().OnMouseDown(event)
            self.modf()(self)
        elif event.button ==1:
            self.annot=self.getPickedAnnotation()
            if self.annot is not None:
                self.annotindex=self.annot.get_zorder()
                self.moveText=True
                mode=self.getAnnotPositionMode(self.annotindex)[0]
                if mode == 'Absolute':
                    self.cursorPosStart=self.__GlobalToRatio(event.x,event.y,self.axes)
                elif mode=='Relative':
                    self.cursorPosStart=self.__GlobalToAxis(event.x,event.y,self.axes)
                self.textPosStart=self.getAnnotPosition(self.annotindex)[0]
                return
            else:
                return super().OnMouseDown(event)
        else:
            return super().OnMouseDown(event)
    def buildContextMenu(self):
        menu = super().constructContextMenu()
        action = menu.exec_(QCursor.pos())
    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        self.keyPressed.emit(e)
    def defModFunc(self,canvas,tab='Axis'):
        from ExtendAnalysis import ModifyWindow, Graph
        parent=self.parentWidget()
        while(parent is not None):
            if isinstance(parent,ExtendMdiSubWindow):
                mod=ModifyWindow(self,parent,showArea=isinstance(parent,Graph))
                mod.selectTab(tab)
                break
            parent=parent.parentWidget()
    @_saveCanvas
    def LoadFromDictionary(self,dictionary,path=home()):
        return super().LoadFromDictionary(dictionary,path)
    def SaveAsDictionary(self,dictionary,path=home()):
        super().SaveAsDictionary(dictionary,path)
    def SaveSetting(self,type):
        dict={}
        self.SaveAsDictionary(dict)
        ExtendCanvas.savedDict[type]=dict[type]
    def LoadSetting(self,type):
        if type in ExtendCanvas.savedDict:
            d={}
            d[type]=ExtendCanvas.savedDict[type]
            self.LoadFromDictionary(d)
