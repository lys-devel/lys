#!/usr/bin/env python
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ExtendAnalysis import *
from .CrosshairAnnot import *
from .CanvasBase import saveCanvas

class AnnotGUICanvas(CrosshairAnnotCanvas, AnnotGUICanvasBase):
    def __init__(self,dpi):
        super().__init__(dpi)
        AnnotGUICanvasBase.__init__(self)
        self.__roi=None
    def constructContextMenu(self):
        menu = super().constructContextMenu()
        return AnnotGUICanvasBase.constructContextMenu(self,menu)
    def _onDrag(self, event, axis=0):
        if event.button()==Qt.LeftButton:
            if self._getMode()=="line":
                return self.__dragLine(event)
            if self._getMode()=="rect":
                return self.__dragRect(event)
        return super()._onDrag(event)
    def __dragLine(self,event):
        if event.isStart():
            self._roi_start=self.axes.mapSceneToView(event.scenePos())
            self.__roi=pg.LineSegmentROI(([0,0],[1,1]))
            self.__roi.setPen(pg.mkPen(color='#000000'))
            self.__roi.setPos(self._roi_start)
            self.__roi.setSize([0,0])
            self.axes.addItem(self.__roi)
            self.__roi.show()
        elif event.isFinish():
            self.axes.removeItem(self.__roi)
            self.addLine([self._roi_start,self._roi_end])
        else:
            self._roi_end=self.axes.mapSceneToView(event.scenePos())
            self.__roi.setSize(self._roi_end-self._roi_start)
        event.accept()
    def __dragRect(self,event):
        if event.isStart():
            self._roi_start=self.axes.mapSceneToView(event.scenePos())
            self.__roi=pg.RectROI([0,0],[1,1])
            self.__roi.setPen(pg.mkPen(color='#000000'))
            self.__roi.setPos(self._roi_start)
            self.__roi.setSize([0,0])
            self.axes.addItem(self.__roi)
            self.__roi.show()
        elif event.isFinish():
            self.axes.removeItem(self.__roi)
            self.addRect(self._roi_start,self._roi_end-self._roi_start)
        else:
            self._roi_end=self.axes.mapSceneToView(event.scenePos())
            self.__roi.setSize(self._roi_end-self._roi_start)
        event.accept()
