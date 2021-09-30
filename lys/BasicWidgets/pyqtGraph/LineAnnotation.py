#!/usr/bin/env python
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from lys import *
from .Annotation import *
from .CanvasBase import saveCanvas


class LineAnnotCanvas(AnnotationSettingCanvas, LineAnnotationCanvasBase):
    def __init__(self, dpi):
        super().__init__(dpi)
        LineAnnotationCanvasBase.__init__(self)
        self.__flg = False

    def SaveAsDictionary(self, dictionary, path):
        super().SaveAsDictionary(dictionary, path)
        LineAnnotationCanvasBase.SaveAsDictionary(self, dictionary, path)

    def LoadFromDictionary(self, dictionary, path):
        super().LoadFromDictionary(dictionary, path)
        LineAnnotationCanvasBase.LoadFromDictionary(self, dictionary, path)

    def _makeLineAnnot(self, pos, axis):
        line = pg.LineSegmentROI(pos)
        line.setPen(pg.mkPen(color='#000000'))
        return line

    def _setLinePosition(self, obj, pos):
        if self.__flg:
            return
        self.__flg = True
        obj.getHandles()[0].setPos(pos[0][0] - obj.pos()[0], pos[1][0] - obj.pos()[1])
        obj.getHandles()[1].setPos(pos[0][1] - obj.pos()[0], pos[1][1] - obj.pos()[1])
        self.__flg = False

    def _getLinePosition(self, obj):
        return [[obj.pos()[0] + obj.listPoints()[0][0], obj.pos()[0] + obj.listPoints()[1][0]], [obj.pos()[1] + obj.listPoints()[0][1], obj.pos()[1] + obj.listPoints()[1][1]]]

    def _addAnnotCallback(self, obj, callback):
        if isinstance(obj, pg.LineSegmentROI):
            obj.sigRegionChanged.connect(lambda obj: callback([[obj.pos()[0] + obj.listPoints()[0][0], obj.pos()[0] + obj.listPoints()[1][0]], [obj.pos()[1] + obj.listPoints()[0][1], obj.pos()[1] + obj.listPoints()[1][1]]]))
            obj.sigRegionChanged.emit(obj)
        else:
            super()._addAnnotCallback(obj, callback)


class InfiniteLineAnnotCanvas(LineAnnotCanvas, InfiniteLineAnnotationCanvasBase):
    def __init__(self, dpi):
        super().__init__(dpi)
        InfiniteLineAnnotationCanvasBase.__init__(self)

    def SaveAsDictionary(self, dictionary, path):
        super().SaveAsDictionary(dictionary, path)
        InfiniteLineAnnotationCanvasBase.SaveAsDictionary(self, dictionary, path)

    def LoadFromDictionary(self, dictionary, path):
        super().LoadFromDictionary(dictionary, path)
        InfiniteLineAnnotationCanvasBase.LoadFromDictionary(self, dictionary, path)

    def _makeInfiniteLineAnnot(self, pos, type, axis):
        if type == 'vertical':
            line = pg.InfiniteLine(pos, 90)
        else:
            line = pg.InfiniteLine(pos, 0)
        line.setMovable(True)
        line.setPen(pg.mkPen(color='#000000'))
        line.setVisible(True)
        return line

    def _getInfiniteLinePosition(self, obj):
        return obj.value()

    def _setInfiniteLinePosition(self, obj, pos):
        return obj.setValue(pos)

    def _addAnnotCallback(self, obj, callback):
        if isinstance(obj, pg.InfiniteLine):
            obj.sigPositionChanged.connect(lambda line: callback(line.value()))
            obj.sigPositionChanged.emit(obj)
        else:
            super()._addAnnotCallback(obj, callback)


class LineAnnotationSettingCanvas(InfiniteLineAnnotCanvas):
    pass
