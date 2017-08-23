#!/usr/bin/env python
import random, sys, os
from enum import Enum
from PyQt5.QtGui import *

from .SaveSettings import *

class ExtendCanvas(SaveSettingCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
        self.modf=weakref.WeakMethod(self.defModFunc)
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
    def OnMouseDown(self, event):
        if event.dblclick:
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
        else:
            return super().OnMouseDown(event)
    def setModificationFunction(self,func):
        self.modf=weakref.WeakMethod(func)
    def buildContextMenu(self):
        menu = super().constructContextMenu()
        action = menu.exec_(QCursor.pos())
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_G:
            if self.modf() is not None:
                self.modf()(self)
    def defModFunc(self,canvas,tab='Axis'):
        from ExtendAnalysis.ModifyWindow import ModifyWindow
        parent=self.parentWidget()
        while(parent is not None):
            if isinstance(parent,ExtendMdiSubWindow):
                mod=ModifyWindow(self,parent,showArea=False)
                mod.selectTab(tab)
                break
            parent=parent.parentWidget()
