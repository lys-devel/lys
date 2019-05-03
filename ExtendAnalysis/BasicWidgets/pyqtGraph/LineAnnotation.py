#!/usr/bin/env python
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ExtendAnalysis import *
from .Annotation import *
from .CanvasBase import saveCanvas

class LineAnnotCanvas(AnnotationSettingCanvas, LineAnnotationCanvasBase):
    def __init__(self,dpi):
        super().__init__(dpi)
        LineAnnotationCanvasBase.__init__(self)
    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        LineAnnotationCanvasBase.SaveAsDictionary(self,dictionary,path)
    def LoadFromDictionary(self,dictionary,path):
        super().LoadFromDictionary(dictionary,path)
        LineAnnotationCanvasBase.LoadFromDictionary(self,dictionary,path)
    def _makeLineAnnot(self,pos,axis):
        line=pg.LineSegmentROI(pos)
        line.setPen(pg.mkPen(color='#000000'))
        return line
    def _getLinePosition(self,obj):
        pos = obj.listPoints()
        return [[pos[0][0],pos[1][0]],[pos[0][1],pos[1][1]]]

class LineAnnotationSettingCanvas(LineAnnotCanvas):
    pass
