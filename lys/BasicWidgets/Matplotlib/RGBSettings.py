#!/usr/bin/env python
import numpy as np

from .CanvasBase import *
from .CanvasBase import saveCanvas


class RGBColorAdjustableCanvas(FigureCanvasBase):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)

    @saveCanvas
    def autoColorRange(self, indexes):
        super().autoColorRange(indexes)
        data = self.getDataFromIndexes(3, indexes)
        for d in data:
            d.appearance['Range'] = (0, np.max(d.wave.data))
            d.modified.emit(d)

    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        if e.key() == Qt.Key_A:
            ids = [i.id for i in self.getRGBs()]
            self.autoColorRange(ids)
            for i in self.getImages():
                i.setColorRange()

    def getColorRange(self, indexes):
        res = super().getColorRange(indexes)
        data = self.getRGBs()
        for d in data:
            if 'Range' in d.appearance:
                res.append(d.appearance['Range'])
            else:
                res.append((0, 1))
        return res

    @saveCanvas
    def setColorRange(self, indexes, min, max, log=False):
        super().setColorRange(indexes, min, max, log)
        data = self.getDataFromIndexes(3, indexes)
        for d in data:
            d.appearance['Range'] = (min, max)
            d.modified.emit(d)

    @saveCanvas
    def setColorRotation(self, indexes, value):
        data = self.getDataFromIndexes(3, indexes)
        for d in data:
            d.appearance['ColorRotation'] = value
            d.modified.emit(d)


class RGBSettingCanvas(RGBColorAdjustableCanvas):
    pass
