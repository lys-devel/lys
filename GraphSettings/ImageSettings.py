#!/usr/bin/env python
import random, weakref, gc, sys, os, math
from ColorWidgets import *
import numpy as np
from ExtendType import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure, SubplotParams
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import colors
from GraphWindow import *
from GraphSettings.LineSettings import *

class ImageColorAdjustableCanvas(MarkerStyleAdjustableCanvas):
    def __init__(self,dpi):
        super().__init__(dpi)
    def saveAppearance(self):
        super().saveAppearance()
        data=self.getImages()
        for d in data:
            d.appearance['Colormap']=d.obj.get_cmap().name
            d.appearance['Range']=(d.obj.norm.vmin,d.obj.norm.vmax)
            d.appearance['Log']=isinstance(d.obj.norm,colors.LogNorm)
    def loadAppearance(self):
        super().loadAppearance()
        data=self.getImages()
        for d in data:
            if 'Colormap' in d.appearance:
                d.obj.set_cmap(d.appearance['Colormap'])
            log=False
            if 'Log' in d.appearance:
                log=d.appearance['Log']
            if 'Range' in d.appearance:
                r=d.appearance['Range']
                if log:
                    norm=colors.LogNorm(vmin=r[0],vmax=r[1])
                else:
                    norm=colors.Normalize(vmin=r[0],vmax=r[1])
                d.obj.set_norm(norm)
    def getColormap(self,indexes):
        res=[]
        data=self.getDataFromIndexes(2,indexes)
        for d in data:
            res.append(d.obj.get_cmap())
        return res
    def setColormap(self,cmap,indexes):
        data=self.getDataFromIndexes(2,indexes)
        for d in data:
            d.obj.set_cmap(cmap)
        self.draw()
    def getColorRange(self,indexes):
        res=[]
        data=self.getDataFromIndexes(2,indexes)
        for d in data:
            res.append((d.obj.norm.vmin,d.obj.norm.vmax))
        return res
    def setColorRange(self,indexes,min,max,log=False):
        data=self.getDataFromIndexes(2,indexes)
        if log:
            norm=colors.LogNorm(vmin=min,vmax=max)
        else:
            norm=colors.Normalize(vmin=min,vmax=max)
        for d in data:
            d.obj.set_norm(norm)
        self.draw()
    def isLog(self,indexes):
        res=[]
        data=self.getDataFromIndexes(2,indexes)
        for d in data:
            res.append(isinstance(d.obj.norm,colors.LogNorm))
        return res
class ImageColorAdjustBox(QWidget):
    class _rangeWidget(QGroupBox):
        valueChanged=pyqtSignal()
        def __init__(self,title,auto=50,mean=50,width=50):
            super().__init__(title)
            self.__mean=mean
            self.__wid=width
            self.__flg=False
            self.__autovalue=auto
            self.__initlayout()
            self.__setAuto()
        def __initlayout(self):
            layout=QVBoxLayout()
            l_h1=QHBoxLayout()
            self.__auto=QPushButton("Auto")
            self.__auto.clicked.connect(self.__setAuto)
            self.__spin1=QDoubleSpinBox()
            self.__spin1.setRange(0,100)
            self.__spin2=QDoubleSpinBox()
            self.__spin2.setRange(-10000000,10000000)
            l_h1.addWidget(QLabel('Rel'))
            l_h1.addWidget(self.__spin1)
            l_h1.addWidget(QLabel('Abs'))
            l_h1.addWidget(self.__spin2)
            l_h1.addWidget(self.__auto)
            layout.addLayout(l_h1)
            self.__slider=QSlider(Qt.Horizontal)
            self.__slider.setRange(0,100)
            layout.addWidget(self.__slider)
            self.__slider.valueChanged.connect(self.__spin1.setValue)
            self.__spin1.valueChanged.connect(self.setRelative)
            self.__spin2.valueChanged.connect(self.setAbsolute)
            self.setLayout(layout)
        def __setAuto(self):
            self.setRelative(self.__autovalue)
        def setRelative(self,val):
            self.__flg=True
            self.__slider.setValue(val)
            self.__spin2.setValue(self.__mean+self.__wid*(val-50)/50)
            self.__flg=False
        def setAbsolute(self,val):
            if not self.__flg:
                self.__spin1.setValue((val-self.__mean)/self.__wid*50+50)
            self.valueChanged.emit()
        def getValue(self):
            return self.__spin2.value()
        def setRange(self,mean,wid):
            self.__mean=mean
            self.__wid=wid
        def setLimit(self,min,max):
            self.__spin2.setRange(min,max)
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        canvas.addDataSelectionListener(self)
        self.__initlayout()
        self.__flg=False
    def __initlayout(self):
        layout=QVBoxLayout()
        self.__cmap=ColormapSelection()
        self.__cmap.colorChanged.connect(self.__changeColormap)
        self.__start=ImageColorAdjustBox._rangeWidget("First",33.33)
        self.__end=ImageColorAdjustBox._rangeWidget("Last",66.66)
        self.__start.valueChanged.connect(self.__changerange)
        self.__end.valueChanged.connect(self.__changerange)
        layout.addWidget(self.__cmap)
        layout.addWidget(self.__start)
        layout.addWidget(self.__end)
        self.setLayout(layout)
    def OnDataSelected(self):
        self.__flg=True
        indexes=self.canvas.getSelectedIndexes(2)
        if len(indexes)==0:
            return
        log=self.canvas.isLog(indexes)[0]
        self.__cmap.setLog(log)
        col=self.canvas.getColormap(indexes)[0]
        self.__cmap.setColormap(col.name)
        im=self.canvas.getDataFromIndexes(2,indexes)[0].wave.data
        self.__start.setRange(im.mean(),math.sqrt(im.var())*5)
        self.__end.setRange(im.mean(),math.sqrt(im.var())*5)
        ran=self.canvas.getColorRange(indexes)[0]
        self.__start.setAbsolute(ran[0])
        self.__end.setAbsolute(ran[1])
        self.__flg=False
    def __changerange(self):
        if not self.__flg:
            indexes=self.canvas.getSelectedIndexes(2)
            self.canvas.setColorRange(indexes,self.__start.getValue(),self.__end.getValue(),self.__cmap.isLog())
            self.__start.setLimit(-float('inf'),self.__end.getValue())
            self.__end.setLimit(self.__start.getValue(),float('inf'))
    def __changeColormap(self):
        if not self.__flg:
            indexes=self.canvas.getSelectedIndexes(2)
            self.canvas.setColormap(self.__cmap.currentColor(),indexes)
            self.__changerange()
