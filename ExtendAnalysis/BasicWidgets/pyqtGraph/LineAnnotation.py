#!/usr/bin/env python
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ExtendAnalysis import *
from .Annotation import *
from .CanvasBase import _saveCanvas

class LineAnnotCanvas(AnnotationSettingCanvas):
    def __init__(self,dpi):
        super().__init__(dpi)
        self._registerType('line')
    @_saveCanvas
    def addLine(self,pos=None,axis=Axis.BottomLeft,appearance=None,id=None,obj=None):
        line=pg.LineSegmentROI(pos)
        line.setPen(pg.mkPen(color='#000000'))
        return self.addAnnotation('line','line',line,appearance=appearance,id=id)
    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        i=0
        dic={}
        self.saveAnnotAppearance()
        for data in self._list['line']:
            dic[i]={}
            dic[i]['Position0']=list(data.obj.listPoints()[0])
            dic[i]['Position1']=list(data.obj.listPoints()[1])
            dic[i]['Appearance']=str(data.appearance)
            i+=1
        dictionary['annot_lines']=dic
    def LoadFromDictionary(self,dictionary,path):
        super().LoadFromDictionary(dictionary,path)
        if 'annot_lines' in dictionary:
            dic=dictionary['annot_lines']
            i=0
            while i in dic:
                p0=dic[i]['Position0']
                p1=dic[i]['Position1']
                p=np.array([p0,p1]).T
                appearance=eval(dic[i]['Appearance'])
                self.addLine(p,axis=Axis.BottomLeft,appearance=appearance)
                i+=1
        self.loadAnnotAppearance()

class LineAnnotColorAdjustableCanvas(LineAnnotCanvas):
    def saveAnnotAppearance(self):
        super().saveAnnotAppearance()
        data=self.getAnnotations('line')
        for d in data:
            d.appearance['LineColor']=d.obj.pen.color().name()
    def loadAnnotAppearance(self):
        super().loadAppearance()
        data=self.getAnnotations('line')
        for d in data:
            if 'LineColor' in d.appearance:
                self.setAnnotLineColor(d.appearance['LineColor'],d.id)
    @_saveCanvas
    def setAnnotLineColor(self,color,indexes):
        data=self.getAnnotationFromIndexes(indexes,'line')
        for d in data:
            d.obj.pen.setColor(QColor(color))
    def getAnnotLineColor(self,indexes):
        res=[]
        data=self.getAnnotationFromIndexes(indexes,'line')
        for d in data:
            res.append(d.obj.pen.color().name())
        return res

class AnnotLineStyleAdjustableCanvas(LineAnnotColorAdjustableCanvas):
    __styles={'solid':Qt.SolidLine,'dashed':Qt.DashLine,'dashdot':Qt.DashDotLine,'dotted':Qt.DotLine,'None':Qt.NoPen}
    __styles_inv = dict((v, k) for k, v in __styles.items())
    def saveAnnotAppearance(self):
        super().saveAnnotAppearance()
        data=self.getAnnotations('line')
        for d in data:
            d.appearance['LineStyle']=self.__styles_inv[d.obj.pen.style()]
            d.appearance['LineWidth']=d.obj.pen.width()
    def loadAnnotAppearance(self):
        super().loadAnnotAppearance()
        data=self.getAnnotations('line')
        for d in data:
            if 'LineStyle' in d.appearance:
                self.setAnnotLineStyle(d.appearance['LineStyle'],d.id)
            if 'LineWidth' in d.appearance:
                self.setAnnotLineWidth(d.appearance['LineWidth'],d.id)
    @_saveCanvas
    def setAnnotLineStyle(self,style,indexes):
        data=self.getAnnotationFromIndexes(indexes,'line')
        for d in data:
            d.obj.pen.setStyle(self.__styles[style])
            d.appearance['OldLineStyle']=self.__styles_inv[d.obj.pen.style()]
    def getAnnotLineStyle(self,indexes):
        res=[]
        data=self.getAnnotationFromIndexes(indexes,'line')
        for d in data:
            res.append(self.__styles_inv[d.obj.pen.style()])
        return res
    @_saveCanvas
    def setAnnotLineWidth(self,width,indexes):
        data=self.getAnnotationFromIndexes(indexes,'line')
        for d in data:
            d.obj.pen.setWidth(width)
        self.draw()
    def getAnnotLineWidth(self,indexes):
        res=[]
        data=self.getAnnotationFromIndexes(indexes,'line')
        for d in data:
            res.append(d.obj.pen.width())
        return res


class LineAnnotationSettingCanvas(AnnotLineStyleAdjustableCanvas):
    pass
