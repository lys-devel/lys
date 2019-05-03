#!/usr/bin/env python
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ExtendAnalysis import *
from .LineAnnotation import *
from .CanvasBase import saveCanvas

class RectAnnotCanvas(LineAnnotationSettingCanvas, RectAnnotationCanvasBase):
    def __init__(self,dpi):
        super().__init__(dpi)
        RectAnnotationCanvasBase.__init__(self)
    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        RectAnnotationCanvasBase.SaveAsDictionary(self,dictionary,path)
    def LoadFromDictionary(self,dictionary,path):
        super().LoadFromDictionary(dictionary,path)
        RectAnnotationCanvasBase.LoadFromDictionary(self,dictionary,path)
    def _makeRectAnnot(self,pos,size,axis):
        roi=pg.RectROI(pos,size)
        roi.setPen(pg.mkPen(color='#000000'))
        return roi
    def _getRectPosition(self,obj):
        return list(obj.pos())
    def _getRectSize(self,obj):
        return list(obj.size())
