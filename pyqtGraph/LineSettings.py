#!/usr/bin/env python
import random, weakref, gc, sys, os
from collections import namedtuple
import numpy as np
from enum import Enum
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure, SubplotParams
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.widgets import RectangleSelector
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import lines, markers

from ExtendAnalysis.ExtendType import *
from ExtendAnalysis.Widgets.ColorWidgets import *
from ExtendAnalysis.GraphWindow import *
from .CanvasBase import *
from .CanvasBase import _saveCanvas

class LineColorAdjustableCanvas(OffsetAdjustableCanvas):
    def saveAppearance(self):
        super().saveAppearance()
        data=self.getLines()
        for d in data:
            d.appearance['LineColor']=d.obj.get_color()
    @_saveCanvas
    def setDataColor(self,color,indexes):
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            d.obj.set_color(color)
        self.draw()
    def getDataColor(self,indexes):
        res=[]
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            res.append(d.obj.get_color())
        return res
    def loadAppearance(self):
        super().loadAppearance()
        data=self.getLines()
        for d in data:
            if 'LineColor' in d.appearance:
                d.obj.set_color(d.appearance['LineColor'])

class LineStyleAdjustableCanvas(LineColorAdjustableCanvas):
    def saveAppearance(self):
        super().saveAppearance()
        data=self.getLines()
        for d in data:
            d.appearance['LineStyle']=d.obj.get_linestyle()
            d.appearance['LineWidth']=d.obj.get_linewidth()
    @_saveCanvas
    def setLineStyle(self,style,indexes):
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            d.obj.set_linestyle(style)
            d.appearance['OldLineStyle']=d.obj.get_linestyle()
        self.draw()
    def getLineStyle(self,indexes):
        res=[]
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            res.append(d.obj.get_linestyle().replace('-.','dashdot').replace('--','dashed').replace('-','solid').replace(':','dotted'))
        return res
    @_saveCanvas
    def setLineWidth(self,width,indexes):
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            d.obj.set_linewidth(width)
        self.draw()
    def getLineWidth(self,indexes):
        res=[]
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            res.append(d.obj.get_linewidth())
        return res
    def loadAppearance(self):
        super().loadAppearance()
        data=self.getLines()
        for d in data:
            if 'LineStyle' in d.appearance:
                d.obj.set_linestyle(d.appearance['LineStyle'])
            if 'LineWidth' in d.appearance:
                d.obj.set_linewidth(d.appearance['LineWidth'])

class MarkerStyleAdjustableCanvas(LineStyleAdjustableCanvas):
    def saveAppearance(self):
        super().saveAppearance()
        data=self.getLines()
        for d in data:
            d.appearance['Marker']=d.obj.get_marker()
            d.appearance['MarkerSize']=d.obj.get_markersize()
            d.appearance['MarkerThick']=d.obj.get_markeredgewidth()
            d.appearance['MarkerFilling']=d.obj.get_fillstyle()
    @_saveCanvas
    def setMarker(self,marker,indexes):
        dummy=lines.Line2D([0,1],[0,1])
        key=list(dummy.markers.keys())
        val=list(dummy.markers.values())
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            d.obj.set_marker(key[val.index(marker)])
            d.appearance['OldMarker']=d.obj.get_marker()
        self.draw()
    def getMarker(self,indexes):
        res=[]
        dummy=lines.Line2D([0,1],[0,1])
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            res.append(dummy.markers[d.obj.get_marker()])
        return res
    @_saveCanvas
    def setMarkerSize(self,size,indexes):
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            d.obj.set_markersize(size)
        self.draw()
    def getMarkerSize(self,indexes):
        res=[]
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            res.append(d.obj.get_markersize())
        return res
    @_saveCanvas
    def setMarkerThick(self,size,indexes):
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            d.obj.set_markeredgewidth(size)
        self.draw()
    def getMarkerThick(self,indexes):
        res=[]
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            res.append(d.obj.get_markeredgewidth())
        return res
    @_saveCanvas
    def setMarkerFilling(self,type,indexes):
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            d.obj.set_fillstyle(type)
        self.draw()
    def getMarkerFilling(self,indexes):
        res=[]
        data=self.getDataFromIndexes(1,indexes)
        for d in data:
            res.append(d.obj.get_fillstyle())
        return res
    def getMarkerList(self):
        dummy=lines.Line2D([0,1],[0,1])
        return dummy.markers
    def getMarkerFillingList(self):
        dummy=lines.Line2D([0,1],[0,1])
        return dummy.fillStyles
    def loadAppearance(self):
        super().loadAppearance()
        data=self.getLines()
        for d in data:
            if 'Marker' in d.appearance:
                d.obj.set_marker(d.appearance['Marker'])
            if 'MarkerSize' in d.appearance:
                d.obj.set_markersize(d.appearance['MarkerSize'])
            if 'MarkerThick' in d.appearance:
                d.obj.set_markeredgewidth(d.appearance['MarkerThick'])
            if 'MarkerFilling' in d.appearance:
                d.obj.set_fillstyle(d.appearance['MarkerFilling'])
