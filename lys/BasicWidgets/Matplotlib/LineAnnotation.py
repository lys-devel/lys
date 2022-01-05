#!/usr/bin/env python
import weakref
import sys
import os
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

    def SaveAsDictionary(self, dictionary, path):
        super().SaveAsDictionary(dictionary, path)
        LineAnnotationCanvasBase.SaveAsDictionary(self, dictionary, path)

    def LoadFromDictionary(self, dictionary, path):
        super().LoadFromDictionary(dictionary, path)
        LineAnnotationCanvasBase.LoadFromDictionary(self, dictionary, path)

    def _makeLineAnnot(self, pos, axis):
        axes = self.getAxes(axis)
        line, = axes.plot((pos[0][0], pos[1][0]), (pos[0][1], pos[1][1]), picker=5)
        return line

    def _getLinePosition(self, obj):
        return obj.get_data()
