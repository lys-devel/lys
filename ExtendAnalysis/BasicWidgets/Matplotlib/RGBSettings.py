#!/usr/bin/env python
import numpy as np

from ExtendAnalysis.ExtendType import *
from .ImageSettings import *

from .CanvasBase import saveCanvas

class RGBColorAdjustableCanvas(ImageSettingCanvas):
    def __init__(self,dpi=100):
        super().__init__(dpi=dpi)
    @saveCanvas
    def autoColorRange(self,indexes):
        super().autoColorRange(indexes)
        data=self.getDataFromIndexes(3,indexes)
        for d in data:
            d.appearance['Range']=(0,np.max(d.wave.data))
            self.OnWaveModified(d.wave)
    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        if e.key() == Qt.Key_A:
            ids = [i.id for i in self.getRGBs()]
            self.autoColorRange(ids)
    def getColorRange(self,indexes):
        res=super().getColorRange(indexes)
        data=self.getRGBs()
        for d in data:
            if 'Range' in d.appearance:
                res.append(d.appearance['Range'])
            else:
                res.append((0,1))
        return res
    @saveCanvas
    def setColorRange(self,indexes,min,max,log=False):
        super().setColorRange(indexes,min,max,log)
        data=self.getDataFromIndexes(3,indexes)
        for d in data:
            d.appearance['Range']=(min,max)
            self.OnWaveModified(d.wave)

    @saveCanvas
    def setColorRotation(self, indexes, value):
        data=self.getDataFromIndexes(3,indexes)
        for d in data:
            d.appearance['ColorRotation']=value
            self.OnWaveModified(d.wave)


class RGBSettingCanvas(RGBColorAdjustableCanvas):
    pass
