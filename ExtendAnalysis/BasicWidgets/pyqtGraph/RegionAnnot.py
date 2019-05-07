#!/usr/bin/env python
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ExtendAnalysis import *
from .RectAnnotation import *
from .CanvasBase import saveCanvas

class RegionAnnotCanvas(RectAnnotCanvas, RegionAnnotationCanvasBase):
    __list={"horizontal": pg.LinearRegionItem.Horizontal, "vertical": pg.LinearRegionItem.Vertical}
    def __init__(self,dpi):
        super().__init__(dpi)
        RegionAnnotationCanvasBase.__init__(self)
    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        RegionAnnotationCanvasBase.SaveAsDictionary(self,dictionary,path)
    def LoadFromDictionary(self,dictionary,path):
        super().LoadFromDictionary(dictionary,path)
        RegionAnnotationCanvasBase.LoadFromDictionary(self,dictionary,path)
    def _makeRegionAnnot(self,region,type,axis):
        roi=pg.LinearRegionItem(region,orientation=self.__list[type])
        return roi
    def _getRegion(self,obj):
        return obj.getRegion()
    def _setLineColor(self,obj,color):
        if isinstance(obj,pg.LinearRegionItem):
            super()._setLineColor(obj.lines[0],color)
            super()._setLineColor(obj.lines[1],color)
        else:
            super()._setLineColor(obj,color)
    def _getLineColor(self,obj):
        if isinstance(obj,pg.LinearRegionItem):
            return super()._getLineColor(obj.lines[0])
        else:
            return super()._getLineColor(obj)
    def _getLineStyle(self,obj):
        if isinstance(obj,pg.LinearRegionItem):
            return super()._getLineStyle(obj.lines[0])
        else:
            return super()._getLineStyle(obj)
    def _setLineStyle(self,obj,style):
        if isinstance(obj,pg.LinearRegionItem):
            return super()._setLineStyle(obj.lines[0],style)
            return super()._setLineStyle(obj.lines[1],style)
        else:
            return super()._setLineStyle(obj,style)
    def _getLineWidth(self,obj):
        if isinstance(obj,pg.LinearRegionItem):
            return super()._getLineWidth(obj.lines[0])
        else:
            return super()._getLineWidth(obj)
    def _setLineWidth(self,obj,width):
        if isinstance(obj,pg.LinearRegionItem):
            return super()._setLineWidth(obj.lines[0],wdith)
            return super()._setLineWidth(obj.lines[1],width)
        else:
            return super()._setLineStyle(obj,width)
    def _addAnnotCallback(self,obj,callback):
        if isinstance(obj,pg.LinearRegionItem):
            obj.sigRegionChanged.connect(lambda roi: callback(roi.getRegion()))
            obj.sigRegionChanged.emit(obj)
        else:
            super()._addAnnotCallback(obj,callback)
