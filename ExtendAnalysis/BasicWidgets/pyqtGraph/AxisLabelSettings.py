#!/usr/bin/env python
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .FontSettings import *
from .CanvasBase import saveCanvas

class AxisLabelAdjustableCanvas(FontSelectableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.addFontChangeListener(self)
    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        dic={}
        for l in ['Left','Right','Top','Bottom']:
            if self.axisIsValid(l):
                dic[l+"_label_on"]=self.getAxisLabelVisible(l)
                dic[l+"_label"]=self.getAxisLabel(l)
                dic[l+"_font"]=self.getAxisLabelFont(l).ToDict()
                dic[l+"_pos"]=self.getAxisLabelCoords(l)
        dictionary['LabelSetting']=dic
    def LoadFromDictionary(self,dictionary,path):
        super().LoadFromDictionary(dictionary,path)
        if 'LabelSetting' in dictionary:
            dic=dictionary['LabelSetting']
            for l in ['Left','Right','Top','Bottom']:
                if self.axisIsValid(l):
                    self.setAxisLabelVisible(l,dic[l+"_label_on"])
                    self.setAxisLabel(l,dic[l+'_label'])
                    self.setAxisLabelFont(l,FontInfo.FromDict(dic[l+"_font"]))
                    self.setAxisLabelCoords(l,dic[l+"_pos"])
    def OnFontChanged(self,name):
        for axis in ['Left','Right','Top','Bottom']:
            if self.axisIsValid(axis):
                self.setAxisLabelFont(axis,self.getFont('Axis'))
    @saveCanvas
    def setAxisLabel(self,axis,text):
        ax=self.fig.getAxis(axis.lower())
        b=self.getAxisLabelVisible(axis)
        ax.setLabel(text)
        self.setAxisLabelVisible(axis,b)
        self._emitAxisRangeChanged()
    def getAxisLabel(self,axis):
        ax=self.fig.getAxis(axis.lower())
        return ax.label.toPlainText()
    @saveCanvas
    def setAxisLabelFont(self,axis,font):
        ax=self.fig.getAxis(axis.lower())
        css={'font-family': font.family, 'font-size': str(font.size)+"pt", "color": font.color}
        ax.setLabel(**css)
        self._emitAxisRangeChanged()
    def getAxisLabelFont(self,axis):
        ax=self.fig.getAxis(axis.lower())
        f=ax.font()
        s=ax.labelStyle
        if "font-family" in s:
            family=s['font-family']
        else:
            family=f.family()
        if "font-size" in s:
            size=int(float(s['font-size'].replace("pt","")))
        else:
            size=f.pointSize()
        if "color" in s:
            color=s['color']
        else:
            color="#ffffff"
        return FontInfo(family,size,color)
    @saveCanvas
    def setAxisLabelVisible(self,axis,b):
        ax=self.fig.getAxis(axis.lower())
        ax.showLabel(b)
        self._emitAxisRangeChanged()
    def getAxisLabelVisible(self,axis):
        ax=self.fig.getAxis(axis.lower())
        return ax.label.isVisible()
    @saveCanvas
    def setAxisLabelCoords(self,axis,pos):
        ax=self.fig.getAxis(axis.lower())
        if axis in ['Left','Right']:
            ax.setStyle(tickTextWidth=int(-pos*100),autoExpandTextSpace=False)
        else:
            ax.setStyle(tickTextHeight=int(-pos*100),autoExpandTextSpace=False)
        self._emitAxisRangeChanged()
    def getAxisLabelCoords(self,axis):
        ax=self.fig.getAxis(axis.lower())
        if axis in ['Left','Right']:
            return -ax.style['tickTextWidth']/100
        else:
            return -ax.style['tickTextHeight']/100

class TickLabelAdjustableCanvas(AxisLabelAdjustableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.addFontChangeListener(self)
    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        dic={}
        for l in ['Left','Right','Top','Bottom']:
            if self.axisIsValid(l):
                dic[l+"_label_on"]=self.getTickLabelVisible(l)
                dic[l+"_font"]=self.getTickLabelFont(l).ToDict()
        dictionary['TickLabelSetting']=dic
    def LoadFromDictionary(self,dictionary,path):
        super().LoadFromDictionary(dictionary,path)
        if 'TickLabelSetting' in dictionary:
            dic=dictionary['TickLabelSetting']
            for l in ['Left','Right','Top','Bottom']:
                if self.axisIsValid(l):
                    self.setTickLabelVisible(l,dic[l+"_label_on"])
                    self.setTickLabelFont(l,FontInfo.FromDict(dic[l+"_font"]))
    def OnFontChanged(self,name):
        super().OnFontChanged(name)
        for axis in ['Left','Right','Top','Bottom']:
            if self.axisIsValid(axis):
                self.setTickLabelFont(axis,self.getFont('Tick'))
    @saveCanvas
    def setTickLabelVisible(self,axis,tf,mirror=False,which='both'):
        if mirror:
            ax=self.fig.getAxis(opposite[axis.lower()])
        else:
            ax=self.fig.getAxis(axis.lower())
        ax.setStyle(showValues=tf)
        self._emitAxisRangeChanged()
    def getTickLabelVisible(self,axis,mirror=False,which='major'):
        if mirror:
            ax=self.fig.getAxis(opposite[axis.lower()])
        else:
            ax=self.fig.getAxis(axis.lower())
        return ax.style['showValues']
    @saveCanvas
    def setTickLabelFont(self,axis,font):
        ax=self.fig.getAxis(axis.lower())
        ax.tickFont=QFont(font.family,font.size)
        self._emitAxisRangeChanged()
    def getTickLabelFont(self,axis):
        ax=self.fig.getAxis(axis.lower())
        f=ax.tickFont
        if f is None:
            return FontInfo.defaultFont()
        else:
            return FontInfo(f.family(),f.pointSize(),"#ffffff")

class AxisSettingCanvas(TickLabelAdjustableCanvas):
    pass
