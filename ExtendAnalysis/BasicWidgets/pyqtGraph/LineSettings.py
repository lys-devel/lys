#!/usr/bin/env python
import random, weakref, gc, sys, os
from collections import namedtuple
import numpy as np
from enum import Enum
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ExtendAnalysis.ExtendType import *
from .CanvasBase import *
from .CanvasBase import saveCanvas

class LineColorAdjustableCanvas(FigureCanvasBase):
    def _setDataColor(self,obj,color):
        obj.setPen(pg.mkPen(color=QColor(color)))
    def _getDataColor(self,obj):
        return self._getLinePen(obj).color().name()
    def _getLinePen(self,obj):
        p=obj.opts['pen']
        if isinstance(p,tuple):
            return pg.mkPen(color=p)
        else:
            return p
    def _getSymbolPen(self,obj):
        p=obj.opts['symbolPen']
        if isinstance(p,tuple):
            return pg.mkPen(color=p)
        else:
            return p
    def _getSymbolBrush(self,obj):
        p=obj.opts['symbolBrush']
        if isinstance(p,tuple):
            return pg.mkBrush(color=p)
        else:
            return p

class LineStyleAdjustableCanvas(LineColorAdjustableCanvas):
    __styles={'solid':Qt.SolidLine,'dashed':Qt.DashLine,'dashdot':Qt.DashDotLine,'dotted':Qt.DotLine,'None':Qt.NoPen}
    __styles_inv = dict((v, k) for k, v in __styles.items())
    def _getLineDataStyle(self,obj):
        return self.__styles_inv[self._getLinePen(obj).style()]
    def _setLineDataStyle(self,obj,style):
        p=self._getLinePen(obj)
        p.setStyle(self.__styles[style])
        obj.setPen(p)
    def _getLineDataWidth(self,obj):
        return self._getLinePen(obj).width()
    def _setLineDataWidth(self,obj,width):
        p=self._getLinePen(obj)
        p.setWidth(width)
        obj.setPen(p)

class MarkerStyleAdjustableCanvas(LineStyleAdjustableCanvas):
    __symbols={"circle":"o", "cross":"x", "tri_down":"t", "tri_up":"t1", "tri_right":"t2", "tri_left":"t3", "square":"s", "pentagon":"p","hexagon":"h", "star":"star", "plus":"+", "diamond":"d", "None":None}
    __symbols_inv = dict((v, k) for k, v in __symbols.items())
    __fillStyles=["full", "None"]
    def _getMarker(self,obj):
        return self.__symbols_inv[obj.opts['symbol']]
    def _getMarkerSize(self,obj):
        return obj.opts['symbolSize']
    def _getMarkerThick(self,obj):
        return self._getSymbolPen(obj).width()
    def _getMarkerFilling(self,obj):
        if self._getSymbolBrush(obj).isOpaque():
            return 'full'
        else:
            return 'None'
    def _setMarker(self,obj,marker):
        obj.setSymbol(self.__symbols[marker])
    def _setMarkerSize(self,obj,size):
        obj.setSymbolSize(size)
    def _setMarkerThick(self,obj,thick):
        p=self._getSymbolPen(obj)
        p.setWidth(thick)
        obj.setSymbolPen(p)
        #for refresh
        p=self._getLinePen(obj)
        obj.setPen(p)
    def _setMarkerFilling(self,obj,filling):
        if filling in ["filled", "full"]:
            c=self._getLinePen(obj).color()
            b=pg.mkBrush(c)
            obj.setSymbolBrush(b)
        else:
            obj.setSymbolBrush(None)
    def getMarkerList(self):
        return self.__symbols_inv
    def getMarkerFillingList(self):
        return self.__fillStyles
