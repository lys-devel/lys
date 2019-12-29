#!/usr/bin/env python
import random, weakref, gc, sys, os, math
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure, SubplotParams
import matplotlib.animation as animation
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import colors

from ExtendAnalysis.ExtendType import *
from .LineSettings import *

from .CanvasBase import saveCanvas

class ImageColorAdjustableCanvas(MarkerStyleAdjustableCanvas):
    def __init__(self,dpi=100):
        super().__init__(dpi=dpi)
    @saveCanvas
    def autoColorRange(self,indexes):
        data=self.getDataFromIndexes(2,indexes)
        for d in data:
            m=d.wave.average()
            v=np.sqrt(d.wave.var())*3
            norm=colors.Normalize(vmin=m-v,vmax=m+v)
            d.obj.set_norm(norm)
        self.draw()
    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        if e.key() == Qt.Key_A:
            ids = [i.id for i in self.getImages()]
            self.autoColorRange(ids)

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
            res.append(d.obj.get_cmap().name)
        return res
    @saveCanvas
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
    @saveCanvas
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

class ImageAnimationCanvas(ImageColorAdjustableCanvas):
    def addImage(self):
        for i in range(1):
            w=Wave()
            w.data=np.random.rand(30,30)
            self.Append(w)
    def StartAnimation(self):
        ims=[]
        lis=self.getWaveData(2)
        for l in lis:
            ims.append([l.obj])
        self.ani=animation.ArtistAnimation(self.fig,ims)
    def StopAnimation(self):
        self.ani.event_source.stop()

class ImageSettingCanvas(ImageAnimationCanvas):
    pass
