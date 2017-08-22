#!/usr/bin/env python
import random, sys, os
from enum import Enum
from PyQt5.QtGui import *

from .AnchorSettings import *
class ExtendCanvas(AnchorSettingCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
        self.modf=None
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
                self.modf('Axis')
                self.setSelectedAxis(self.__findAxis(axis))
                return super().OnMouseDown(event)
            line=self.getPickedLine()
            if line is not None:
                self.modf('Lines')
                w=self.getWaveDataFromArtist(line)
                self.setSelectedIndexes(1,w.id)
                return super().OnMouseDown(event)
            image=self.getPickedImage()
            if image is not None:
                self.modf('Images')
                w=self.getWaveDataFromArtist(image)
                self.setSelectedIndexes(2,w.id)
                return super().OnMouseDown(event)
            self.modf()
        else:
            return super().OnMouseDown(event)
    def setModificationFunction(self,func):
        self.modf=func
    def buildContextMenu(self):
        menu = super().constructContextMenu()
        action = menu.exec_(QCursor.pos())
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_G:
            if self.modf is not None:
                self.modf()
