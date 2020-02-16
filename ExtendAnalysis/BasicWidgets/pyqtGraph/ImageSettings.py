#!/usr/bin/env python
import random
import weakref
import gc
import sys
import os
import math
import numpy as np
from matplotlib import cm
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ExtendAnalysis.ExtendType import *
from .LineSettings import *

from .CanvasBase import saveCanvas


class ImageColorAdjustableCanvas(MarkerStyleAdjustableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)

    @saveCanvas
    def autoColorRange(self, indexes):
        data = self.getDataFromIndexes(2, indexes)
        for d in data:
            d.obj.setImage(d.wave.data, autoLevels=True)

    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        if e.key() == Qt.Key_A:
            ids = [i.id for i in self.getImages()]
            self.autoColorRange(ids)

    def saveAppearance(self):
        super().saveAppearance()
        data = self.getImages()
        for d in data:
            d.appearance['Range'] = list(d.obj.getLevels())

    def loadAppearance(self):
        super().loadAppearance()
        data = self.getImages()
        for d in data:
            if 'Colormap' in d.appearance:
                colormap = cm.get_cmap(d.appearance['Colormap'])
                colormap._init()
                lut = np.array(colormap._lut * 255)
                lut = lut[0:lut.shape[0] - 3, :]
                self.__setColor(d, lut)
            if 'Range' in d.appearance:
                d.obj.setLevels(d.appearance['Range'])

    def getColormap(self, indexes):
        res = []
        data = self.getDataFromIndexes(2, indexes)
        for d in data:
            if 'Colormap' in d.appearance:
                res.append(d.appearance['Colormap'])
            else:
                res.append('gray')
        return res

    @saveCanvas
    def setColormap(self, cmap, indexes):
        data = self.getDataFromIndexes(2, indexes)
        colormap = cm.get_cmap(cmap)
        colormap._init()
        lut = np.array(colormap._lut * 255)
        lut = lut[0:lut.shape[0] - 3, :]
        for d in data:
            self.__setColor(d, lut)
            d.appearance['Colormap'] = cmap

    def __setColor(self, d, lut):
        if 'Log' in d.appearance:
            if d.appearance['Log']:
                d.obj.setImage(np.log(d.wave.data), lut=lut)
            else:
                d.obj.setImage(d.wave.data, lut=lut)
        else:
            d.obj.setImage(d.wave.data, lut=lut)

    def getColorRange(self, indexes):
        res = []
        data = self.getDataFromIndexes(2, indexes)
        for d in data:
            res.append(d.obj.getLevels())
        return res

    @saveCanvas
    def setColorRange(self, indexes, min, max, log=False):
        data = self.getDataFromIndexes(2, indexes)
        for d in data:
            if log:
                d.appearance['Log'] = True
                d.obj.setImage(np.log(d.wave.data), levels=(min, max))
            else:
                d.appearance['Log'] = False
                d.obj.setImage(d.wave.data, levels=(min, max))

    def isLog(self, indexes):
        res = []
        data = self.getDataFromIndexes(2, indexes)
        for d in data:
            if 'Log' in d.appearance:
                res.append(d.appearance['Log'])
            else:
                res.append(False)
        return res


class ImagePlaneAdjustableCanvas(ImageColorAdjustableCanvas):
    def setIndex(self, indexes, zindex):
        data = self.getDataFromIndexes(2, indexes)[0]
        data.zindex = zindex
        self.OnWaveModified(data.wave)
        self.setSelectedIndexes(2, data.id)


class ImageAnimationCanvas(ImagePlaneAdjustableCanvas):
    def addImage(self):
        pass

    def StartAnimation(self):
        print("Animation is not implemented.")

    def StopAnimation(self):
        print("Animation is not implemented.")


class ImageSettingCanvas(ImageAnimationCanvas, RGBColorAdjustableCanvasBase):
    pass
