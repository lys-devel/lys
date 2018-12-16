#!/usr/bin/env python
import random, weakref, sys, os
import numpy as np
from enum import Enum
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure, SubplotParams
import matplotlib as mpl
import matplotlib.font_manager as fm
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import lines, markers, ticker

from ExtendAnalysis import *
from .FontSettings import *
from .CanvasBase import _saveCanvas

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
    @_saveCanvas
    def setAxisLabel(self,axis,text):
        axes=self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left','Right']:
            axes.get_yaxis().get_label().set_text(text)
        else:
            axes.get_xaxis().get_label().set_text(text)
        self.draw()
    def getAxisLabel(self,axis):
        axes=self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left','Right']:
            return axes.get_ylabel()
        else:
            return axes.get_xlabel()
    @_saveCanvas
    def setAxisLabelFont(self,axis,font):
        axes=self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left','Right']:
            axes.get_yaxis().get_label().set_family(font.family)
            axes.get_yaxis().get_label().set_size(font.size)
            axes.get_yaxis().get_label().set_color(font.color)
        else:
            axes.get_xaxis().get_label().set_family(font.family)
            axes.get_xaxis().get_label().set_size(font.size)
            axes.get_xaxis().get_label().set_color(font.color)
        self.draw()
    def getAxisLabelFont(self,axis):
        axes=self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left','Right']:
            label=axes.get_yaxis().get_label()
        else:
            label=axes.get_xaxis().get_label()
        return FontInfo(label.get_family()[0],label.get_size(),label.get_color())
    @_saveCanvas
    def setAxisLabelVisible(self,axis,b):
        axes=self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left','Right']:
            axes.get_yaxis().get_label().set_visible(b)
        else:
            axes.get_xaxis().get_label().set_visible(b)
        self.draw()
    def getAxisLabelVisible(self,axis):
        axes=self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left','Right']:
            return axes.get_yaxis().get_label().get_visible()
        else:
            return axes.get_xaxis().get_label().get_visible()
    @_saveCanvas
    def setAxisLabelCoords(self,axis,pos):
        axes=self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left','Right']:
            axes.get_yaxis().set_label_coords(pos,0.5)
        else:
            axes.get_xaxis().set_label_coords(0.5,pos)
        self.draw()
    def getAxisLabelCoords(self,axis):
        axes=self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left','Right']:
            pos=axes.get_yaxis().get_label().get_position()
            if pos[0]>1:
                return axes.transAxes.inverted().transform(pos)[0]
            else:
                return pos[0]
        else:
            pos=axes.get_xaxis().get_label().get_position()
            if pos[1]>1:
                return axes.transAxes.inverted().transform(pos)[1]
            else:
                return pos[1]
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
    @_saveCanvas
    def setTickLabelVisible(self,axis,tf,mirror=False,which='both'):
        axes=self.getAxes(axis)
        if axes is None:
            return
        if tf:
            value="on"
        else:
            value="off"
        if (axis == 'Left' and not mirror) or (axis == 'Right' and mirror):
            axes.get_yaxis().set_tick_params(labelleft=value,which=which)
        if (axis == 'Right' and not mirror) or (axis == 'Left' and mirror):
            axes.get_yaxis().set_tick_params(labelright=value,which=which)
        if (axis == 'Top' and not mirror) or (axis == 'Bottom' and mirror):
            axes.get_xaxis().set_tick_params(labeltop=value,which=which)
        if (axis == 'Bottom' and not mirror) or (axis == 'Top' and mirror):
            axes.get_xaxis().set_tick_params(labelbottom=value,which=which)
        self.draw()
    def getTickLabelVisible(self,axis,mirror=False,which='major'):
        axs=self.getAxes(axis)
        if axis in ['Left','Right']:
            ax=axs.get_yaxis()
        if axis in ['Bottom','Top']:
            ax=axs.get_xaxis()
        if which=='major':
            tick=ax.get_major_ticks()[0]
        elif which=='minor':
            tick=ax.get_minor_ticks()[0]
        if axis in ['Left','Bottom']:
            if mirror:
                return tick.label2On
            else:
                return tick.label1On
        else:
            if mirror:
                return tick.label1On
            else:
                return tick.label2On
    @_saveCanvas
    def setTickLabelFont(self,axis,font):
        axes=self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left','Right']:
            for tick in axes.get_xticklabels():
                tick.set_fontname(font.family)
            axis='x'
        else:
            for tick in axes.get_yticklabels():
                tick.set_fontname(font.family)
            axis='y'
        axes.tick_params(which='major',labelsize=font.size,color=font.color,axis=axis)
        self.draw()
    def getTickLabelFont(self,axis):
        axes=self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left','Right']:
            tick=axes.get_yaxis().get_major_ticks()[0]
        else:
            tick=axes.get_xaxis().get_major_ticks()[0]
        l=tick.label1
        return FontInfo(l.get_family()[0],l.get_size(),l.get_color())
class AxisSettingCanvas(TickLabelAdjustableCanvas):
    pass
