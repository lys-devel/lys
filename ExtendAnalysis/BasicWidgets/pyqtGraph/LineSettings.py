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

class LineColorAdjustableCanvas(OffsetAdjustableCanvas):
    def saveAppearance(self):
        super().saveAppearance()
        data=self.getLines()
        for d in data:
            d.appearance['LineColor']=self._getLinePen(d.obj).color().name()
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
    @saveCanvas
    def setDataColor(self,color,indexes):
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            p=self._getLinePen(d.obj)
            p.setColor(QColor(color))
            d.obj.setPen(p)
    def getDataColor(self,indexes):
        return [self._getLinePen(d.obj).color().name() for d in self.getDataFromIndexes(1,indexes)]
    def loadAppearance(self):
        super().loadAppearance()
        data=self.getLines()
        for d in data:
            if 'LineColor' in d.appearance:
                d.obj.setPen(pg.mkPen(color=QColor(d.appearance['LineColor'])))

class LineStyleAdjustableCanvas(LineColorAdjustableCanvas):
    __styles={'solid':Qt.SolidLine,'dashed':Qt.DashLine,'dashdot':Qt.DashDotLine,'dotted':Qt.DotLine,'None':Qt.NoPen}
    __styles_inv = dict((v, k) for k, v in __styles.items())
    def saveAppearance(self):
        super().saveAppearance()
        data=self.getLines()
        for d in data:
            d.appearance['LineStyle']=self.__styles_inv[self._getLinePen(d.obj).style()]
            d.appearance['LineWidth']=self._getLinePen(d.obj).width()
    @saveCanvas
    def setLineStyle(self,style,indexes):
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            p=self._getLinePen(d.obj)
            p.setStyle(self.__styles[style])
            d.obj.setPen(p)
    def getLineStyle(self,indexes):
        return [self.__styles_inv[self._getLinePen(d.obj).style()] for d in self.getDataFromIndexes(1,indexes)]
    @saveCanvas
    def setLineWidth(self,width,indexes):
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            p=self._getLinePen(d.obj)
            p.setWidth(width)
            d.obj.setPen(p)
    def getLineWidth(self,indexes):
        return [self._getLinePen(d.obj).width() for d in self.getDataFromIndexes(1,indexes)]
    def loadAppearance(self):
        super().loadAppearance()
        data=self.getLines()
        for d in data:
            if 'LineStyle' in d.appearance:
                self._getLinePen(d.obj).setStyle(self.__styles[d.appearance['LineStyle']])
            if 'LineWidth' in d.appearance:
                self._getLinePen(d.obj).setWidth(d.appearance['LineWidth'])

class MarkerStyleAdjustableCanvas(LineStyleAdjustableCanvas):
    __symbols={"circle":"o", "cross":"x", "tri_down":"t", "tri_up":"t1", "tri_right":"t2", "tri_left":"t3", "square":"s", "pentagon":"p","hexagon":"h", "star":"star", "plus":"+", "diamond":"d", "None":None}
    __symbols_inv = dict((v, k) for k, v in __symbols.items())
    __fillStyles=["filled", "None"]
    def saveAppearance(self):
        super().saveAppearance()
        data=self.getLines()
        for d in data:
            d.appearance['Marker']=self.__symbols_inv[d.obj.opts['symbol']]
            d.appearance['MarkerSize']=d.obj.opts['symbolSize']
            d.appearance['MarkerThick']=self._getSymbolPen(d.obj).width()
            d.appearance['MarkerFilling']=self._getSymbolBrush(d.obj).isOpaque()
    @saveCanvas
    def setMarker(self,marker,indexes):
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            d.obj.setSymbol(self.__symbols[marker])
    def getMarker(self,indexes):
        return [self.__symbols_inv[d.obj.opts['symbol']] for d in self.getDataFromIndexes(1,indexes)]
    @saveCanvas
    def setMarkerSize(self,size,indexes):
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            d.obj.setSymbolSize(size)
    def getMarkerSize(self,indexes):
        return [d.obj.opts['symbolSize'] for d in self.getDataFromIndexes(1,indexes)]
    @saveCanvas
    def setMarkerThick(self,size,indexes):
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            p=self._getSymbolPen(d.obj)
            p.setWidth(size)
            d.obj.setSymbolPen(p)
            #for refresh
            p=self._getLinePen(d.obj)
            d.obj.setPen(p)
    def getMarkerThick(self,indexes):
        return [self._getSymbolPen(d.obj).width() for d in self.getDataFromIndexes(1,indexes)]
    @saveCanvas
    def setMarkerFilling(self,type,indexes):
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            if type=="filled":
                c=self._getLinePen(d.obj).color()
                b=pg.mkBrush(c)
                d.obj.setSymbolBrush(b)
            else:
                d.obj.setSymbolBrush(None)
    def getMarkerFilling(self,indexes):
        res=[]
        for d in self.getDataFromIndexes(1,indexes):
            if self._getSymbolBrush(d.obj).isOpaque():
                res.append('filled')
            else:
                res.append('None')
        return res
    def getMarkerList(self):
        return self.__symbols_inv
    def getMarkerFillingList(self):
        return self.__fillStyles
    def loadAppearance(self):
        super().loadAppearance()
        data=self.getLines()
        for d in data:
            if 'MarkerThick' in d.appearance:
                p=self._getSymbolPen(d.obj)
                p.setWidth(d.appearance['MarkerThick'])
                d.obj.setSymbolPen(p)
            if 'Marker' in d.appearance:
                d.obj.setSymbol(self.__symbols[d.appearance['Marker']])
            if 'MarkerSize' in d.appearance:
                d.obj.setSymbolSize(d.appearance['MarkerSize'])
            if 'MarkerFilling' in d.appearance:
                if d.appearance['MarkerFilling']:
                    c=self._getLinePen(d.obj).color()
                    b=pg.mkBrush(c)
                    d.obj.setSymbolBrush(b)
                else:
                    d.obj.setSymbolBrush(None)
