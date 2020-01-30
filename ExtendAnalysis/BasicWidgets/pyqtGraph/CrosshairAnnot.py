#!/usr/bin/env python
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ExtendAnalysis import *
from .RegionAnnot import *
from .CanvasBase import saveCanvas
from .CrosshairItem import *


class CrosshairAnnotCanvas(RegionAnnotCanvas, CrosshairAnnotationCanvasBase):
    def __init__(self, dpi):
        super().__init__(dpi)
        CrosshairAnnotationCanvasBase.__init__(self)

    def SaveAsDictionary(self, dictionary, path):
        super().SaveAsDictionary(dictionary, path)
        CrosshairAnnotationCanvasBase.SaveAsDictionary(self, dictionary, path)

    def LoadFromDictionary(self, dictionary, path):
        super().LoadFromDictionary(dictionary, path)
        CrosshairAnnotationCanvasBase.LoadFromDictionary(self, dictionary, path)

    def _makeCrossAnnot(self, pos, axis):
        roi = CrosshairItem(pos)
        return roi

    def _getPosition(self, obj):
        return obj.getPosition()

    def _setLineColor(self, obj, color):
        if isinstance(obj, CrosshairItem):
            super()._setLineColor(obj.lines[0], color)
            super()._setLineColor(obj.lines[1], color)
        else:
            super()._setLineColor(obj, color)

    def _getLineColor(self, obj):
        if isinstance(obj, CrosshairItem):
            return super()._getLineColor(obj.lines[0])
        else:
            return super()._getLineColor(obj)

    def _getLineStyle(self, obj):
        if isinstance(obj, CrosshairItem):
            return super()._getLineStyle(obj.lines[0])
        else:
            return super()._getLineStyle(obj)

    def _setLineStyle(self, obj, style):
        if isinstance(obj, CrosshairItem):
            return super()._setLineStyle(obj.lines[0], style)
            return super()._setLineStyle(obj.lines[1], style)
        else:
            return super()._setLineStyle(obj, style)

    def _getLineWidth(self, obj):
        if isinstance(obj, CrosshairItem):
            return super()._getLineWidth(obj.lines[0])
        else:
            return super()._getLineWidth(obj)

    def _setLineWidth(self, obj, width):
        if isinstance(obj, CrosshairItem):
            return super()._setLineWidth(obj.lines[0], wdith)
            return super()._setLineWidth(obj.lines[1], width)
        else:
            return super()._setLineStyle(obj, width)

    def _addAnnotCallback(self, obj, callback):
        if isinstance(obj, CrosshairItem):
            obj.sigRegionChanged.connect(lambda roi: callback(roi.getPosition()))
        else:
            super()._addAnnotCallback(obj, callback)
