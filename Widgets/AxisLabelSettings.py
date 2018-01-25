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
from .ColorWidgets import *
from .AxisSettings import *
from .CanvasBase import _saveCanvas

class FontInfo(object):
    _fonts=None
    def __init__(self,family,size=10,color='black'):
        self.family=str(family)
        self.size=size
        self.color=color
    def ToDict(self):
        dic={}
        dic['family']=self.family
        dic['size']=self.size
        dic['color']=self.color
        return dic
    @classmethod
    def FromDict(cls,dic):
        return FontInfo(dic['family'],dic['size'],dic['color'])
    @classmethod
    def loadFonts(cls):
        if cls._fonts is not None:
            return
        fonts = fm.findSystemFonts()
        cls._fonts=[]
        for f in fonts:
            n=fm.FontProperties(fname=f).get_name()
            if not n in cls._fonts:
                cls._fonts.append(n)
            cls._fonts=sorted(cls._fonts)

class FontSelectableCanvas(TickAdjustableCanvas):
    def __init__(self,dpi=100):
        super().__init__(dpi=dpi)
        self.__font={}
        self.__def={}
        self.__font['Default']=FontInfo(fm.FontProperties(family=mpl.rcParams['font.family']).get_name())
        self.__def['Default']=False
        self.__listener=[]
    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        dic={}
        dic_def={}
        for name in self.__font.keys():
            dic[name]=self.__font[name].ToDict()
            dic_def[name]=self.__def[name]
        dictionary['Font']=dic
        dictionary['Font_def']=dic_def
    def LoadFromDictionary(self,dictionary,path):
        super().LoadFromDictionary(dictionary,path)
        if 'Font' in dictionary:
            dic=dictionary['Font']
            dic_def=dictionary['Font_def']
            for d in dic.keys():
                self.__font[d]=FontInfo.FromDict(dic[d])
                self.__def[d]=dic_def[d]
    def addFontChangeListener(self,listener):
        self.__listener.append(weakref.ref(listener))
    def _emit(self,name):
        for l in self.__listener:
            if l() is None:
                self.__listener.remove(l)
            else:
                l().OnFontChanged(name)
    @_saveCanvas
    def addFont(self,name):
        if not name in self.__font:
            self.__font[name]=FontInfo(self.__font['Default'].family)
            self.__def[name]=True
    def getFont(self,name='Default'):
        if name in self.__font:
            if not self.__def[name]:
                return self.__font[name]
        return self.__font['Default']
    @_saveCanvas
    def setFont(self,font,name='Default'):
        self.__font[name]=font
        self._emit(name)
    @_saveCanvas
    def setFontDefault(self,b,name):
        self.__def[name]=b
        self._emit(name)
    def getFontDefault(self,name):
        if name in self.__font:
            if not self.__def[name]:
                return False
        return True
class FontSelectBox(QGroupBox):
    def __init__(self,canvas,name='Default'):
        super().__init__(name+' Font')
        self.canvas=canvas
        canvas.addFont(name)
        self.__flg=False
        self.__name=name
        FontInfo.loadFonts()
        self.__initlayout()
        self.__loadstate()
        self.canvas.addFontChangeListener(self)
    def OnFontChanged(self,name):
        if name==self.__name or name=='Default':
            self.__loadstate()
    def __initlayout(self):
        layout=QVBoxLayout()
        l=QHBoxLayout()
        self.__font=QComboBox()
        font=self.canvas.getFont(self.__name)
        d=font.family
        for f in FontInfo._fonts:
            self.__font.addItem(f)
        if not d in FontInfo._fonts:
            self.__font.addItem(d)
        self.__font.activated.connect(self.__fontChanged)
        layout.addWidget(self.__font)
        self.__def=QCheckBox('Use default')
        self.__def.stateChanged.connect(self.__setdefault)
        if not self.__name=='Default':
            l.addWidget(self.__def)
        l.addWidget(QLabel('Size'))
        self.__size=QDoubleSpinBox()
        self.__size.valueChanged.connect(self.__fontChanged)
        l.addWidget(self.__size)
        l.addWidget(QLabel('Color'))
        self.__color=ColorSelection()
        self.__color.colorChanged.connect(self.__fontChanged)
        l.addWidget(self.__color)
        layout.addLayout(l)
        self.setLayout(layout)
    def __loadstate(self):
        self.__flg=True
        font=self.canvas.getFont(self.__name)
        if font.family in FontInfo._fonts:
            self.__font.setCurrentIndex(FontInfo._fonts.index(font.family))
        self.__size.setValue(font.size)
        self.__color.setColor(font.color)
        self.__def.setChecked(self.canvas.getFontDefault(self.__name))
        self.__flg=False
    def __fontChanged(self):
        if self.__flg:
            return
        font=FontInfo(self.__font.currentText(),self.__size.value(),self.__color.getColor())
        self.canvas.setFont(font,self.__name)
    def __setdefault(self):
        if self.__flg:
            return
        val=self.__def.isChecked()
        self.canvas.setFontDefault(val,self.__name)
class FontSelectWidget(QGroupBox):
    fontChanged=pyqtSignal()
    def __init__(self,canvas,name='Default'):
        super().__init__('Font')
        self.canvas=canvas
        self.__name=name
        FontInfo.loadFonts()
        self.__initlayout()
        self.setFont(self.canvas.getFont(self.__name))
        self.setFontDefault(True)
        self.canvas.addFontChangeListener(self)
    def OnFontChanged(self,name):
        if name==self.__name and self.__def.isChecked():
            self.setFont(self.canvas.getFont(self.__name))
    def __initlayout(self):
        layout=QVBoxLayout()
        l=QHBoxLayout()
        self.__font=QComboBox()

        for f in FontInfo._fonts:
            self.__font.addItem(f)
        font=self.canvas.getFont(self.__name)
        d=font.family
        if not d in FontInfo._fonts:
            self.__font.addItem(d)
        self.__font.activated.connect(self.__Changed)
        layout.addWidget(self.__font)
        self.__def=QCheckBox('Use default')
        self.__def.stateChanged.connect(self.__Changed)
        l.addWidget(self.__def)
        l.addWidget(QLabel('Size'))
        self.__size=QDoubleSpinBox()
        self.__size.valueChanged.connect(self.__Changed)
        l.addWidget(self.__size)
        l.addWidget(QLabel('Color'))
        self.__color=ColorSelection()
        self.__color.colorChanged.connect(self.__Changed)
        l.addWidget(self.__color)
        layout.addLayout(l)
        self.setLayout(layout)
    def getFont(self):
        if self.__def.isChecked():
            return self.canvas.getFont(self.__name)
        return FontInfo(self.__font.currentText(),self.__size.value(),self.__color.getColor())
    def setFont(self,font):
        if font.family in FontInfo._fonts:
            self.__font.setCurrentIndex(FontInfo._fonts.index(font.family))
            self.__size.setValue(font.size)
            self.__color.setColor(font.color)
    def setFontDefault(self,b):
        self.__def.setChecked(b)
    def getFontDefault(self):
        return self.__def.isChecked()
    def __Changed(self):
        if self.__def.isChecked():
            self.setFont(self.canvas.getFont(self.__name))
        self.fontChanged.emit()

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
class AxisLabelAdjustBox(QGroupBox):
    def __init__(self,canvas):
        super().__init__("Axis Label")
        self.__flg=False
        self.canvas=canvas
        self.__initlayout()
        self.__loadstate()
        self.canvas.addAxisSelectedListener(self)
    def __getAxes(self):
        if self.__all.isChecked():
            return ['Left','Right','Bottom','Top']
        else:
            return [self.canvas.getSelectedAxis()]
    def __initlayout(self):
        l=QVBoxLayout()
        lay=QHBoxLayout()
        self.__all=QCheckBox('All axes')
        lay.addWidget(self.__all)
        self.__on=QCheckBox('Put label')
        self.__on.stateChanged.connect(self.__visible)
        lay.addWidget(self.__on)
        lay.addWidget(QLabel('Position'))
        self.__pos=QDoubleSpinBox()
        self.__pos.setRange(-10,10)
        self.__pos.setSingleStep(0.02)
        self.__pos.valueChanged.connect(self.__posChanged)
        lay.addWidget(self.__pos)
        l.addLayout(lay)
        self.__label=QTextEdit()
        self.__label.setMinimumHeight(10)
        self.__label.setMaximumHeight(50)
        self.__label.textChanged.connect(self.__labelChanged)
        l.addWidget(self.__label)
        self.setLayout(l)
    def __loadstate(self):
        self.__flg=True
        axis=self.canvas.getSelectedAxis()
        self.__on.setChecked(self.canvas.getAxisLabelVisible(axis))
        self.__label.setPlainText(self.canvas.getAxisLabel(axis))
        self.__pos.setValue(self.canvas.getAxisLabelCoords(axis))
        self.__flg=False
    def OnAxisSelected(self,axis):
        self.__loadstate()
    def __labelChanged(self):
        if self.__flg:
            return
        axis=self.canvas.getSelectedAxis()
        self.canvas.setAxisLabel(axis,self.__label.toPlainText())
    def __visible(self):
        if self.__flg:
            return
        for axis in self.__getAxes():
            self.canvas.setAxisLabelVisible(axis,self.__on.isChecked())
    def __posChanged(self):
        if self.__flg:
            return
        for axis in self.__getAxes():
            self.canvas.setAxisLabelCoords(axis,self.__pos.value())

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
class TickLabelAdjustBox(QGroupBox):
    def __init__(self,canvas):
        super().__init__("Tick Label")
        self.__flg=False
        self.canvas=canvas
        self.__initlayout()
        self.__loadstate()
        self.canvas.addAxisSelectedListener(self)
    def __getAxes(self):
        if self.__all.isChecked():
            return ['Left','Right','Bottom','Top']
        else:
            return [self.canvas.getSelectedAxis()]
    def __initlayout(self):
        l=QVBoxLayout()
        lay=QHBoxLayout()
        self.__all=QCheckBox('All axes')
        lay.addWidget(self.__all)
        self.__on=QCheckBox('Put label')
        self.__on.stateChanged.connect(self.__visible)
        lay.addWidget(self.__on)
        l.addLayout(lay)
        self.setLayout(l)
    def __loadstate(self):
        self.__flg=True
        axis=self.canvas.getSelectedAxis()
        self.__on.setChecked(self.canvas.getTickLabelVisible(axis))
        self.__flg=False
    def OnAxisSelected(self,axis):
        self.__loadstate()
    def __visible(self):
        if self.__flg:
            return
        for axis in self.__getAxes():
            self.canvas.setTickLabelVisible(axis,self.__on.isChecked())

class AxisAndTickLabelBox(QWidget):
    def __init__(self,canvas):
        super().__init__()
        layout=QVBoxLayout(self)
        layout.addWidget(FontSelectBox(canvas))
        layout.addWidget(AxisLabelAdjustBox(canvas))
        layout.addWidget(TickLabelAdjustBox(canvas))
        self.setLayout(layout)
class AxisFontBox(QWidget):
    def __init__(self,canvas):
        super().__init__()
        layout=QVBoxLayout(self)
        layout.addWidget(FontSelectBox(canvas))
        layout.addWidget(FontSelectBox(canvas,'Axis'))
        layout.addWidget(FontSelectBox(canvas,'Tick'))
        self.setLayout(layout)
class AxisSettingCanvas(TickLabelAdjustableCanvas):
    pass
