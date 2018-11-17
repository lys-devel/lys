#!/usr/bin/env python
import random, weakref, gc, sys, os
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure, SubplotParams
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import colors, patches
from matplotlib.patches import BoxStyle
import matplotlib

from ExtendAnalysis.ExtendType import *
from ExtendAnalysis import *

from .Annotation import *
from .CanvasBase import _saveCanvas

class LineAnnotCanvas(AnnotationSettingCanvas):
    def __init__(self,dpi):
        super().__init__(dpi)
        self._registerType('line')
    @_saveCanvas
    def addLine(self,pos,axis=Axis.BottomLeft,appearance=None,id=None):
        axes=self._getAxesFrom(axis)
        a,=axes.plot((pos[0][0],pos[1][0]),(pos[0][1],pos[1][1]),picker=5)
        return self.addAnnotation('line','line',a,appearance=appearance,id=id)
    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        i=0
        dic={}
        self.saveAnnotAppearance()
        for data in self._list['line']:
            dic[i]={}
            dic[i]['Position0']=list(data.obj.get_data()[0])
            dic[i]['Position1']=list(data.obj.get_data()[1])
            dic[i]['Appearance']=str(data.appearance)
            if data.obj.axes==self.axes:
                axis=1
            if data.obj.axes==self.axes_ty:
                axis=2
            if data.obj.axes==self.axes_tx:
                axis=3
            if data.obj.axes==self.axes_txy:
                axis=4
            dic[i]['Axis']=axis
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
                axis=dic[i]['Axis']
                if axis==1:
                    axis=Axis.BottomLeft
                if axis==2:
                    axis=Axis.TopLeft
                if axis==3:
                    axis=Axis.BottomRight
                if axis==4:
                    axis=Axis.TopRight
                self.addLine(p,axis=axis,appearance=appearance)
                i+=1
        self.loadAnnotAppearance()

class LineAnnotColorAdjustableCanvas(LineAnnotCanvas):
    def saveAnnotAppearance(self):
        super().saveAnnotAppearance()
        data=self.getAnnotations('line')
        for d in data:
            d.appearance['LineColor']=d.obj.get_color()
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
            d.obj.set_color(color)
        self.draw()
    def getAnnotLineColor(self,indexes):
        res=[]
        data=self.getAnnotationFromIndexes(indexes,'line')
        for d in data:
            res.append(d.obj.get_color())
        return res
class LineAnnotColorAdjustBox(ColorSelection):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        canvas.addAnnotationSelectedListener(self)
        self.colorChanged.connect(self.__changed)
    def OnClicked(self):
        indexes=self.canvas.getSelectedAnnotations('line')
        cols=self.canvas.getAnnotLineColor(indexes)
        if len(cols)==0:
            return
        super().OnClicked()
    def __changed(self):
        indexes=self.canvas.getSelectedAnnotations('line')
        cols=self.canvas.getAnnotLineColor(indexes)
        if len(cols)==0:
            return
        self.canvas.setAnnotLineColor(self.getColor(),indexes)
    def OnAnnotationSelected(self):
        indexes=self.canvas.getSelectedAnnotations('line')
        if len(indexes)==0:
            return
        cols=self.canvas.getAnnotLineColor(indexes)
        self.setColor(cols[0])

class AnnotLineStyleAdjustableCanvas(LineAnnotColorAdjustableCanvas):
    def saveAnnotAppearance(self):
        super().saveAnnotAppearance()
        data=self.getAnnotations('line')
        for d in data:
            d.appearance['LineStyle']=d.obj.get_linestyle()
            d.appearance['LineWidth']=d.obj.get_linewidth()
    def loadAnnotAppearance(self):
        super().loadAnnotAppearance()
        data=self.getAnnotations('line')
        for d in data:
            if 'LineStyle' in d.appearance:
                d.obj.set_linestyle(d.appearance['LineStyle'])
            if 'LineWidth' in d.appearance:
                d.obj.set_linewidth(d.appearance['LineWidth'])
    @_saveCanvas
    def setAnnotLineStyle(self,style,indexes):
        data=self.getAnnotationFromIndexes(indexes,'line')
        for d in data:
            d.obj.set_linestyle(style)
            d.appearance['OldLineStyle']=d.obj.get_linestyle()
        self.draw()
    def getAnnotLineStyle(self,indexes):
        res=[]
        data=self.getAnnotationFromIndexes(indexes,'line')
        for d in data:
            res.append(d.obj.get_linestyle().replace('-.','dashdot').replace('--','dashed').replace('-','solid').replace(':','dotted'))
        return res
    @_saveCanvas
    def setAnnotLineWidth(self,width,indexes):
        data=self.getAnnotationFromIndexes(indexes,'line')
        for d in data:
            d.obj.set_linewidth(width)
        self.draw()
    def getAnnotLineWidth(self,indexes):
        res=[]
        data=self.getAnnotationFromIndexes(indexes,'line')
        for d in data:
            res.append(d.obj.get_linewidth())
        return res
class AnnotLineStyleAdjustBox(QGroupBox):
    __list=['solid','dashed','dashdot','dotted','None']
    def __init__(self,canvas):
        super().__init__("Line")
        self.canvas=canvas
        canvas.addAnnotationSelectedListener(self)

        layout=QGridLayout()
        self.__combo=QComboBox()
        self.__combo.addItems(AnnotLineStyleAdjustBox.__list)
        self.__combo.activated.connect(self.__changeStyle)
        self.__spin1=QDoubleSpinBox()
        self.__spin1.valueChanged.connect(self.__valueChange)

        layout.addWidget(QLabel('Type'),0,0)
        layout.addWidget(self.__combo,1,0)
        layout.addWidget(QLabel('Width'),0,1)
        layout.addWidget(self.__spin1,1,1)

        self.setLayout(layout)

    def __changeStyle(self):
        indexes=self.canvas.getSelectedAnnotations('line')
        if len(indexes)==0:
            return
        res=self.__combo.currentText()
        self.canvas.setAnnotLineStyle(res,indexes)
    def __valueChange(self):
        indexes=self.canvas.getSelectedAnnotations('line')
        if len(indexes)==0:
            return
        self.canvas.setAnnotLineWidth(self.__spin1.value(),indexes)
    def OnAnnotationSelected(self):
        indexes=self.canvas.getSelectedAnnotations('line')
        if len(indexes)==0:
            return
        cols=self.canvas.getAnnotLineStyle(indexes)
        res=cols[0]
        self.__combo.setCurrentIndex(AnnotLineStyleAdjustBox.__list.index(res))
        wids=self.canvas.getAnnotLineWidth(indexes)
        self.__spin1.setValue(wids[0])

class LineAnnotGUICanvas(AnnotLineStyleAdjustableCanvas):
    def __init__(self,dpi):
        super().__init__(dpi)
        self.__draw=False
        self.__drawflg=False
    def constructContextMenu(self):
        menu = super().constructContextMenu()
        m=menu.addMenu('Tools')
        m.addAction(QAction('Select Range',self,triggered=self.__enddraw))
        m.addAction(QAction('Draw Line',self,triggered=self.__startdraw))
        return menu
    def __startdraw(self):
        self.__draw=True
    def __enddraw(self):
        self.__draw=False
    def __GlobalToAxis(self, x, y, ax):
        loc=self.__GlobalToRatio(x,y,ax)
        xlim=ax.get_xlim()
        ylim=ax.get_ylim()
        x_ax=xlim[0]+(xlim[1]-xlim[0])*loc[0]
        y_ax=ylim[0]+(ylim[1]-ylim[0])*loc[1]
        return [x_ax,y_ax]
    def __GlobalToRatio(self, x, y, ax):
        ran=ax.get_position()
        x_loc=(x - ran.x0 * self.width())/((ran.x1 - ran.x0)*self.width())
        y_loc=(y - ran.y0 * self.height())/((ran.y1 - ran.y0)*self.height())
        return [x_loc,y_loc]
    def OnMouseDown(self, event):
        if not self.__draw:
            return super().OnMouseDown(event)
        if event.button == 1:
            self.__drawflg=True
            #self.__saved = self.copy_from_bbox(self.axes.bbox)
            ax=self.__GlobalToAxis(event.x,event.y,self.axes)
            self._pos_start=ax
            self.__line,=self.axes.plot([ax[0]],[ax[1]])
    def OnMouseUp(self, event):
        if not self.__draw:
            return super().OnMouseUp(event)
        if self.__drawflg == True and event.button == 1:
            ax=self.__GlobalToAxis(event.x,event.y,self.axes)
            if not self._pos_start==ax:
                self.addLine((self._pos_start,ax))
            self.__line.set_data([],[])
            self.draw()
            self.__drawflg=False
    def OnMouseMove(self, event):
        if not self.__draw:
            return super().OnMouseMove(event)
        if self.__drawflg == True:
            ax=self.__GlobalToAxis(event.x,event.y,self.axes)
            self.__line.set_data([self._pos_start[0],ax[0]],[self._pos_start[1],ax[1]])
            self.draw()

class LineAnnotationBox(QWidget):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        layout=QVBoxLayout()
        layout.addWidget(AnnotationSelectionBox(canvas,'line'))
        tab=QTabWidget()
        lv1=QVBoxLayout()
        lv1.addWidget(LineAnnotColorAdjustBox(canvas))
        lv1.addWidget(AnnotLineStyleAdjustBox(canvas))
        w=QWidget()
        w.setLayout(lv1)
        tab.addTab(w,'Appearance')
        layout.addWidget(tab)
        self.setLayout(layout)
class LineAnnotationSettingCanvas(LineAnnotGUICanvas):
    pass
