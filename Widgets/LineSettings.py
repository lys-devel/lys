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
from .ColorWidgets import *
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
class LineColorAdjustBox(ColorSelection):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        canvas.addDataSelectionListener(self)
        self.colorChanged.connect(self.__changed)
    def OnClicked(self):
        indexes=self.canvas.getSelectedIndexes(1)
        cols=self.canvas.getDataColor(indexes)
        if len(cols)==0:
            return
        super().OnClicked()
    def __changed(self):
        indexes=self.canvas.getSelectedIndexes(1)
        cols=self.canvas.getDataColor(indexes)
        if len(cols)==0:
            return
        self.canvas.setDataColor(self.getColor(),indexes)
    def OnDataSelected(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        cols=self.canvas.getDataColor(indexes)
        self.setColor(cols[0])

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
class LineStyleAdjustBox(QGroupBox):
    __list=['solid','dashed','dashdot','dotted','None']
    def __init__(self,canvas):
        super().__init__("Line")
        self.canvas=canvas
        canvas.addDataSelectionListener(self)

        layout=QGridLayout()
        self.__combo=QComboBox()
        self.__combo.addItems(LineStyleAdjustBox.__list)
        self.__combo.activated.connect(self.__changeStyle)
        self.__spin1=QDoubleSpinBox()
        self.__spin1.valueChanged.connect(self.__valueChange)

        layout.addWidget(QLabel('Type'),0,0)
        layout.addWidget(self.__combo,1,0)
        layout.addWidget(QLabel('Width'),0,1)
        layout.addWidget(self.__spin1,1,1)

        self.setLayout(layout)

    def __changeStyle(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        res=self.__combo.currentText()
        self.canvas.setLineStyle(res,indexes)
    def __valueChange(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        self.canvas.setLineWidth(self.__spin1.value(),indexes)
    def OnDataSelected(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        cols=self.canvas.getLineStyle(indexes)
        res=cols[0]
        self.__combo.setCurrentIndex(LineStyleAdjustBox.__list.index(res))
        wids=self.canvas.getLineWidth(indexes)
        self.__spin1.setValue(wids[0])

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
class MarkerStyleAdjustBox(QGroupBox):
    def __init__(self,canvas):
        super().__init__("Marker")
        self.canvas=canvas
        self.__list=list(canvas.getMarkerList().values())
        self.__fillist=canvas.getMarkerFillingList()
        canvas.addDataSelectionListener(self)
        self.__initlayout()

    def __initlayout(self):
        gl=QGridLayout()

        self.__combo=QComboBox()
        self.__combo.addItems(self.__list)
        self.__combo.activated.connect(self.__changeStyle)
        self.__spin1=QDoubleSpinBox()
        self.__spin1.valueChanged.connect(self.__sizeChange)
        self.__fill=QComboBox()
        self.__fill.addItems(self.__fillist)
        self.__fill.activated.connect(self.__changeFilling)
        self.__spin2=QDoubleSpinBox()
        self.__spin2.valueChanged.connect(self.__thickChange)

        gl.addWidget(QLabel('Type'),0,0)
        gl.addWidget(self.__combo,1,0)
        gl.addWidget(QLabel('Size'),2,0)
        gl.addWidget(self.__spin1,3,0)
        gl.addWidget(QLabel('Filling'),0,1)
        gl.addWidget(self.__fill,1,1)
        gl.addWidget(QLabel('Thick'),2,1)
        gl.addWidget(self.__spin2,3,1)
        self.setLayout(gl)

    def __changeStyle(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        res=self.__combo.currentText()
        self.canvas.setMarker(res,indexes)
    def __changeFilling(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        res=self.__fill.currentText()
        self.canvas.setMarkerFilling(res,indexes)
    def __sizeChange(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        res=self.__spin1.value()
        self.canvas.setMarkerSize(res,indexes)
    def __thickChange(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        res=self.__spin2.value()
        self.canvas.setMarkerThick(res,indexes)
    def OnDataSelected(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        cols=self.canvas.getMarker(indexes)
        self.__combo.setCurrentIndex(self.__list.index(cols[0]))
        cols=self.canvas.getMarkerSize(indexes)
        self.__spin1.setValue(cols[0])
        cols=self.canvas.getMarkerThick(indexes)
        self.__spin2.setValue(cols[0])
        cols=self.canvas.getMarkerFilling(indexes)
        self.__fill.setCurrentIndex(self.__fillist.index(cols[0]))

class ApperanceBox(QWidget):
    def __init__(self,canvas):
        super().__init__()
        layout=QVBoxLayout()

        layout_h1=QHBoxLayout()
        layout_h1.addWidget(QLabel('Color'))
        layout_h1.addWidget(LineColorAdjustBox(canvas))
        layout.addLayout(layout_h1)
        layout.addWidget(LineStyleAdjustBox(canvas))
        layout.addWidget(MarkerStyleAdjustBox(canvas))

        self.setLayout(layout)
