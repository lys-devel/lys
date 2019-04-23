#!/usr/bin/env python
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ExtendAnalysis import *
from .LineAnnotation import *
from .CanvasBase import _saveCanvas

class RectAnnotCanvas(LineAnnotationSettingCanvas):
    def __init__(self,dpi):
        super().__init__(dpi)
        self._registerType('rect')
    @_saveCanvas
    def addRect(self,pos,size,axis=Axis.BottomLeft,appearance=None,id=None):
        roi=pg.RectROI(pos,size)
        roi.setPen(pg.mkPen(color='#000000'))
        return self.addAnnotation('rect','rect',roi,appearance=appearance,id=id)
    def addCallback(self,indexes,callback):
        list=self.getAnnotations('rect',indexes)
        for l in list:
            l.obj.sigRegionChanged.connect(callback)
    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        i=0
        dic={}
        self.saveAnnotAppearance()
        for data in self._list['rect']:
            dic[i]={}
            dic[i]['Position']=list(data.obj.pos())
            dic[i]['Size']=list(data.obj.size())
            dic[i]['Appearance']=str(data.appearance)
            i+=1
        dictionary['annot_rect']=dic
    def LoadFromDictionary(self,dictionary,path):
        super().LoadFromDictionary(dictionary,path)
        if 'annot_rect' in dictionary:
            dic=dictionary['annot_rect']
            i=0
            while i in dic:
                p=dic[i]['Position']
                s=dic[i]['Size']
                appearance=eval(dic[i]['Appearance'])
                self.addCross(p,s,axis=Axis.BottomLeft,appearance=appearance)
                i+=1
        self.loadAnnotAppearance()

class RectAnnotColorAdjustableCanvas(RectAnnotCanvas):
    def saveAnnotAppearance(self):
        super().saveAnnotAppearance()
        data=self.getAnnotations('rect')
        for d in data:
            d.appearance['Color']=d.obj.pen.color().name()
    def loadAnnotAppearance(self):
        super().loadAppearance()
        data=self.getAnnotations('rect')
        for d in data:
            if 'Color' in d.appearance:
                self.setAnnotLineColor(d.appearance['Color'],d.id)
    @_saveCanvas
    def setAnnotLineColor(self,color,indexes):
        data=self.getAnnotationFromIndexes(indexes,'rect')
        for d in data:
            d.obj.pen.setColor(QColor(color))
    def getAnnotLineColor(self,indexes):
        res=[]
        data=self.getAnnotationFromIndexes(indexes,'rect')
        for d in data:
            res.append(d.obj.pen.color().name())
        return res

class AnnotRectStyleAdjustableCanvas(RectAnnotColorAdjustableCanvas):
    __styles={'solid':Qt.SolidLine,'dashed':Qt.DashLine,'dashdot':Qt.DashDotLine,'dotted':Qt.DotLine,'None':Qt.NoPen}
    __styles_inv = dict((v, k) for k, v in __styles.items())
    def saveAnnotAppearance(self):
        super().saveAnnotAppearance()
        data=self.getAnnotations('rect')
        for d in data:
            d.appearance['LineStyle']=self.__styles_inv[d.obj.pen.style()]
            d.appearance['LineWidth']=d.obj.pen.width()
    def loadAnnotAppearance(self):
        super().loadAnnotAppearance()
        data=self.getAnnotations('rect')
        for d in data:
            if 'LineStyle' in d.appearance:
                self.setAnnotLineStyle(d.appearance['LineStyle'],d.id)
            if 'LineWidth' in d.appearance:
                self.setAnnotLineWidth(d.appearance['LineWidth'],d.id)
    @_saveCanvas
    def setAnnotLineStyle(self,style,indexes):
        data=self.getAnnotationFromIndexes(indexes,'rect')
        for d in data:
            d.obj.pen.setStyle(self.__styles[style])
            d.appearance['OldLineStyle']=self.__styles_inv[d.obj.pen.style()]
    def getAnnotLineStyle(self,indexes):
        res=[]
        data=self.getAnnotationFromIndexes(indexes,'rect')
        for d in data:
            res.append(self.__styles_inv[d.obj.pen.style()])
        return res
    @_saveCanvas
    def setAnnotLineWidth(self,width,indexes):
        data=self.getAnnotationFromIndexes(indexes,'rect')
        for d in data:
            d.obj.pen.setWidth(width)
        self.draw()
    def getAnnotLineWidth(self,indexes):
        res=[]
        data=self.getAnnotationFromIndexes(indexes,'rect')
        for d in data:
            res.append(d.obj.pen.width())
        return res

class AnnotGUICanvas(AnnotRectStyleAdjustableCanvas):
    def __init__(self,dpi):
        super().__init__(dpi)
        self.__mode="range"
        self.__roi=None
    def constructContextMenu(self):
        menu = super().constructContextMenu()
        m=menu.addMenu('Tools')
        m.addAction(QAction('Select Range',self,triggered=self.__range))
        m.addAction(QAction('Draw Line',self,triggered=self.__line))
        m.addAction(QAction('Draw Rectangle',self,triggered=self.__rect))
        return menu
    def __line(self):
        self.__mode="line"
    def __range(self):
        self.__mode="range"
    def __rect(self):
        self.__mode="rect"
    def _onDrag(self, event, axis=0):
        if event.button()==Qt.LeftButton:
            if self.__mode=="line":
                return self.__dragLine(event)
            if self.__mode=="rect":
                return self.__dragRect(event)
        return super()._onDrag(event)
    def __dragLine(self,event):
        if event.isStart():
            self._roi_start=self.axes.mapSceneToView(event.scenePos())
            self.__roi=pg.LineSegmentROI(([0,0],[1,1]))
            self.__roi.setPen(pg.mkPen(color='#000000'))
            self.__roi.setPos(self._roi_start)
            self.axes.addItem(self.__roi)
            self.__roi.show()
        elif event.isFinish():
            self.axes.removeItem(self.__roi)
            self.addLine([self._roi_start,self._roi_end])
        else:
            self._roi_end=self.axes.mapSceneToView(event.scenePos())
            self.__roi.setSize(self._roi_end-self._roi_start)
        event.accept()
    def __dragRect(self,event):
        if event.isStart():
            self._roi_start=self.axes.mapSceneToView(event.scenePos())
            self.__roi=pg.RectROI([0,0],[1,1])
            self.__roi.setPen(pg.mkPen(color='#000000'))
            self.__roi.setPos(self._roi_start)
            self.axes.addItem(self.__roi)
            self.__roi.show()
        elif event.isFinish():
            self.axes.removeItem(self.__roi)
            self.addRect(self._roi_start,self._roi_end-self._roi_start)
        else:
            self._roi_end=self.axes.mapSceneToView(event.scenePos())
            self.__roi.setSize(self._roi_end-self._roi_start)
        event.accept()


class RectAnnotationSettingCanvas(AnnotGUICanvas):
    pass
