#!/usr/bin/env python
import random, weakref, gc, sys, os, math
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure, SubplotParams
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import colors

from ExtendAnalysis.ExtendType import *
from .ColorWidgets import *
from ExtendAnalysis.GraphWindow import *
from .AxisLabelSettings import *
from .CanvasBase import _saveCanvas, _notSaveCanvas

class MarginAdjustableCanvas(AxisSettingCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.__listener=[]
        self.setMargin()
    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        dictionary['Margin']=self.margins
    def LoadFromDictionary(self,dictionary,path):
        super().LoadFromDictionary(dictionary,path)
        if 'Margin' in dictionary:
            m=dictionary['Margin']
            self.setMargin(left=m[0],right=m[1],bottom=m[2],top=m[3])
    @_saveCanvas
    def setMargin(self,left=0, right=0, bottom=0, top=0):
        l=left
        r=right
        t=top
        b=bottom
        if l==0:
            l=0.2
        if r==0:
            if self.axes_tx is None and self.axes_txy is None:
                r=0.85
            else:
                r=0.80
        if b==0:
            b=0.2
        if t==0:
            if self.axes_ty is None and self.axes_txy is None:
                t=0.85
            else:
                t=0.80
        if l>=r:
            r=l+0.05
        if b>=t:
            t=b+0.05
        self.fig.subplots_adjust(left=l, right=r, top=t, bottom=b)
        self.margins=[left,right,bottom,top]
        self.margins_act=[l,r,b,t]
        for l in self.__listener:
            if l() is not None:
                l().OnMarginAdjusted()
            else:
                self.__listener.remove(l)
        self.draw()
    def getMargin(self):
        return self.margins
    def getActualMargin(self):
        return self.margins_act
    def addMarginAdjustedListener(self,listener):
        self.__listener.append(weakref.ref(listener))
class MarginAdjustBox(QGroupBox):
    def __init__(self,canvas):
        super().__init__("Margin (0 means auto)")
        self.canvas=canvas
        self._initlayout(canvas)
    def _valueChanged(self):
        self.canvas.setMargin(self._left.value(),self._right.value(),self._bottom.value(),self._top.value())
    def _initlayout(self,canvas):
        m=canvas.getMargin()
        lv=QVBoxLayout()

        lh1=QHBoxLayout()
        lh1.addWidget(QLabel('Left'))
        self._left=QDoubleSpinBox()
        self._left.setRange(0,1)
        self._left.setSingleStep(0.05)
        self._left.setValue(m[0])
        self._left.valueChanged.connect(self._valueChanged)
        lh1.addWidget(self._left)
        lh1.addWidget(QLabel('Right'))
        self._right=QDoubleSpinBox()
        self._right.setRange(0,1)
        self._right.setSingleStep(0.05)
        self._right.setValue(m[1])
        self._right.valueChanged.connect(self._valueChanged)
        lh1.addWidget(self._right)

        lh2=QHBoxLayout()
        lh2.addWidget(QLabel('Bottom'))
        self._bottom=QDoubleSpinBox()
        self._bottom.setRange(0,1)
        self._bottom.setSingleStep(0.05)
        self._bottom.setValue(m[2])
        self._bottom.valueChanged.connect(self._valueChanged)
        lh2.addWidget(self._bottom)
        lh2.addWidget(QLabel('Top'))
        self._top=QDoubleSpinBox()
        self._top.setRange(0,1)
        self._top.setSingleStep(0.05)
        self._top.setValue(m[3])
        self._top.valueChanged.connect(self._valueChanged)
        lh2.addWidget(self._top)

        lv.addLayout(lh1)
        lv.addLayout(lh2)
        self.setLayout(lv)

unit=0.3937007874#inch->cm
class ResizableCanvas(MarginAdjustableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.__wmode='Auto'
        self.__hmode='Auto'
        self.__wvalue=0
        self.__waxis1='Left'
        self.__waxis2='Bottom'
        self.__hvalue=0
        self.__haxis1='Left'
        self.__haxis2='Bottom'
        self.__listener=[]
        self.setAbsoluteSize(4,4)
        self.setAutoSize()
        self.addMarginAdjustedListener(self)
        self.addAxisRangeChangeListener(self.OnAxisRangeChanged)

    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        dic={}
        size=self.getSize()
        if self.__wmode=='Auto':
            self.__wvalue=size[0]
        if self.__hmode=='Auto':
            self.__hvalue=size[1]
        dic['Width']=[self.__wmode,self.__wvalue,self.__waxis1,self.__waxis2]
        dic['Height']=[self.__hmode,self.__hvalue,self.__haxis1,self.__haxis2]
        dictionary['Size']=dic
    def LoadFromDictionary(self,dictionary,path):
        super().LoadFromDictionary(dictionary,path)
        if 'Size' in dictionary:
            dic=dictionary['Size']
            if dic['Width'][0] in ['Aspect','Plan']:
                self.setSizeByArray(dic['Height'],'Height',True)
                self.setSizeByArray(dic['Width'],'Width',True)
            else:
                self.setSizeByArray(dic['Width'],'Width',True)
                self.setSizeByArray(dic['Height'],'Height',True)
    def OnMarginAdjusted(self):
        self.setSizeByArray([self.__wmode,self.__wvalue,self.__waxis1,self.__waxis2],'Width')
        self.setSizeByArray([self.__hmode,self.__hvalue,self.__haxis1,self.__haxis2],'Height')
    def setSizeByArray(self,array,axis,loaded=False):
        if axis=='Width':
            self.__wmode=array[0]
            self.__wvalue=array[1]
            self.__waxis1=array[2]
            self.__waxis2=array[3]
            if self.__wmode=='Auto':
                if loaded:
                    self._setAbsWid(self.__wvalue)
                self.setAutoWidth()
            elif self.__wmode=='Absolute':
                self.setAbsoluteWidth(self.__wvalue)
            elif self.__wmode=='Per Unit':
                self.setWidthPerUnit(self.__wvalue,self.__waxis1)
            elif self.__wmode=='Aspect':
                self.setWidthForHeight(self.__wvalue)
            elif self.__wmode=='Plan':
                self.setWidthPlan(self.__wvalue,self.__waxis1,self.__waxis2)
        else:
            self.__hmode=array[0]
            self.__hvalue=array[1]
            self.__haxis1=array[2]
            self.__haxis2=array[3]
            if self.__hmode=='Auto':
                if loaded:
                    self._setAbsHei(self.__hvalue)
                self.setAutoHeight()
            elif self.__hmode=='Absolute':
                self.setAbsoluteHeight(self.__hvalue)
            elif self.__hmode=='Per Unit':
                self.setHeightPerUnit(self.__hvalue,self.__haxis1)
            elif self.__hmode=='Aspect':
                self.setHeightForWidth(self.__hvalue)
            elif self.__hmode=='Plan':
                self.setHeightPlan(self.__hvalue,self.__haxis1,self.__haxis2)
    def getMarginRatio(self):
        m=self.getActualMargin()
        wr=1/(m[1]-m[0])
        hr=1/(m[3]-m[2])
        return (wr,hr)
    def _adjust(self):
        par=self.parentWidget()
        self.resize(self.fig.get_figwidth()*100,self.fig.get_figheight()*100)
        if isinstance(par,SizeAdjustableWindow):
            par.adjustSize()
        self.draw()

    def _unfixAxis(self,axis):
        par=self.parentWidget()
        if axis=='Width':
            param=self.getSizeParams('Height')
            if isinstance(par,SizeAdjustableWindow):
                par.setWidth(0)
        else:
            param=self.getSizeParams('Width')
            if isinstance(par,SizeAdjustableWindow):
                par.setHeight(0)
        if not (param[0]=='Plan' or param[0]=='Aspect'):
            self.axes.set_aspect('auto')
    @_saveCanvas
    def setAutoWidth(self):
        self.__wmode='Auto'
        self._unfixAxis('Width')
        self._emitResizeEvent()
    @_saveCanvas
    def setAutoHeight(self):
        self.__hmode='Auto'
        self._unfixAxis('Height')
        self._emitResizeEvent()
    @_saveCanvas
    def setAutoSize(self):
        self.setAutoWidth()
        self.setAutoHeight()
    @_saveCanvas
    def setAbsoluteWidth(self,width):
        if width==0:
            return
        self.__wmode='Absolute'
        self.__wvalue=width
        self._setAbsWid(width)
    @_saveCanvas
    def setAbsoluteHeight(self,height):
        if height==0:
            return
        self.__hmode='Absolute'
        self.__hvalue=height
        self._setAbsHei(height)
    @_saveCanvas
    def setAbsoluteSize(self,width,height):
        self.setAbsoluteWidth(width)
        self.setAbsoluteHeight(height)
    @_saveCanvas
    def setWidthPerUnit(self,value,axis):
        if value==0:
            return
        self.__wmode='Per Unit'
        self.__wvalue=value
        self.__waxis1=axis
        ran=self.getAxisRange(axis)
        self._setAbsWid(value*abs(ran[1]-ran[0]))
    @_saveCanvas
    def setHeightPerUnit(self,value,axis):
        if value==0:
            return
        self.__hmode='Per Unit'
        self.__hvalue=value
        self.__haxis1=axis
        ran=self.getAxisRange(axis)
        self._setAbsHei(value*abs(ran[1]-ran[0]))

    def _setAbsWid(self,width):
        par=self.parentWidget()
        param=self.getSizeParams('Height')
        if not (param[0]=='Aspect' or param[0]=='Plan'):
            self.axes.set_aspect('auto')
        rat=self.getMarginRatio()
        self.fig.set_figwidth(width*unit*rat[0])
        if param[0]=='Aspect' or param[0]=='Plan':
            ran1=self.getAxisRange('Bottom')
            ran2=self.getAxisRange('Left')
            self.fig.set_figheight(self.axes.get_aspect()*(rat[1]/rat[0])*abs(ran2[1]-ran2[0])/abs(ran1[1]-ran1[0])*self.fig.get_figwidth())
            if isinstance(par,SizeAdjustableWindow):
                par.setHeight(0)
        if isinstance(par,SizeAdjustableWindow):
            par.setWidth(0)
        self._adjust()
        if isinstance(par,SizeAdjustableWindow):
            par.setWidth(par.width())
            if param[0]=='Aspect' or param[0]=='Plan':
                par.setHeight(par.height())
        self._emitResizeEvent()
    def _setAbsHei(self,height):
        par=self.parentWidget()
        param=self.getSizeParams('Width')
        if not (param[0]=='Aspect' or param[0]=='Plan'):
            self.axes.set_aspect('auto')
        rat=self.getMarginRatio()
        self.fig.set_figheight(height*unit*rat[1])
        if param[0]=='Aspect' or param[0]=='Plan':
            ran1=self.getAxisRange('Bottom')
            ran2=self.getAxisRange('Left')
            self.fig.set_figwidth(1/self.axes.get_aspect()*(rat[0]/rat[1])*abs(ran1[1]-ran1[0])/abs(ran2[1]-ran2[0])*self.fig.get_figheight())
            if isinstance(par,SizeAdjustableWindow):
                par.setWidth(0)
        if isinstance(par,SizeAdjustableWindow):
            par.setHeight(0)
        self._adjust()
        if isinstance(par,SizeAdjustableWindow):
            par.setHeight(par.height())
            if param[0]=='Aspect' or param[0]=='Plan':
                par.setWidth(par.width())
        self._emitResizeEvent()
    @_saveCanvas
    def parentResized(self):
        wp=self.getSizeParams('Width')
        hp=self.getSizeParams('Height')
        if (wp[0]=='Aspect' or wp[0]=='Plan') and hp[0]=='Auto':
            self.setSizeByArray(wp,'Width')
        if (hp[0]=='Aspect' or hp[0]=='Plan') and wp[0]=='Auto':
            self.setSizeByArray(hp,'Height')
    @_saveCanvas
    def setWidthForHeight(self,aspect):
        if aspect==0:
            return
        self.__wmode='Aspect'
        self.__wvalue=aspect
        self._widthForHeight(aspect)
    @_saveCanvas
    def setHeightForWidth(self,aspect):
        if aspect==0:
            return
        self.__hmode='Aspect'
        self.__hvalue=aspect
        self._heightForWidth(aspect)
    @_saveCanvas
    def setWidthPlan(self,aspect,axis1,axis2):
        if aspect==0:
            return
        self.__wmode='Plan'
        self.__wvalue=aspect
        self.__waxis1=axis1
        self.__waxis2=axis2
        ran1=self.getAxisRange(axis1)
        ran2=self.getAxisRange(axis2)
        self._widthForHeight(aspect*abs(ran1[1]-ran1[0])/abs(ran2[1]-ran2[0]))
    @_saveCanvas
    def setHeightPlan(self,aspect,axis1,axis2):
        if aspect==0:
            return
        self.__hmode='Plan'
        self.__hvalue=aspect
        self.__haxis1=axis1
        self.__haxis2=axis2
        ran1=self.getAxisRange(axis1)
        ran2=self.getAxisRange(axis2)
        self._heightForWidth(aspect*abs(ran1[1]-ran1[0])/abs(ran2[1]-ran2[0]))

    def _widthForHeight(self,aspect):
        self._unfixAxis('Width')
        rat=self.getMarginRatio()
        ran1=self.getAxisRange('Bottom')
        ran2=self.getAxisRange('Left')
        self.axes.set_aspect(1/aspect*abs(ran1[1]-ran1[0])/abs(ran2[1]-ran2[0]))
        param=self.getSizeParams('Height')
        if param[0]=='Auto':
            self.fig.set_figwidth(self.fig.get_figheight()*rat[0]/rat[1])
        if param[0]=='Absolute' or param[0]=='Per Unit':
            self.setSizeByArray(param,'Height')
        self._adjust()
        self._emitResizeEvent()
    def _heightForWidth(self,aspect):
        self._unfixAxis('Height')
        rat=self.getMarginRatio()
        ran1=self.getAxisRange('Left')
        ran2=self.getAxisRange('Bottom')
        self.axes.set_aspect(aspect*abs(ran2[1]-ran2[0])/abs(ran1[1]-ran1[0]))
        param=self.getSizeParams('Width')
        if param[0]=='Auto':
            self.fig.set_figheight(self.fig.get_figwidth()*rat[1]/rat[0])
        if param[0]=='Absolute' or param[0]=='Per Unit':
            self.setSizeByArray(param,'Width')
        self._adjust()
        self._emitResizeEvent()
    def getSize(self):
        rat=self.getMarginRatio()
        w=self.fig.get_figwidth()
        h=self.fig.get_figheight()
        return (w/rat[0]/unit,h/rat[1]/unit)
    def getSizeParams(self,wh):
        if wh=='Width':
            return (self.__wmode,self.__wvalue,self.__waxis1,self.__waxis2)
        else:
            return (self.__hmode,self.__hvalue,self.__haxis1,self.__haxis2)
    @_notSaveCanvas
    def RestoreSize(self):
        self.setSizeByArray(self.getSizeParams('Width'),'Width',True)
        self.setSizeByArray(self.getSizeParams('Height'),'Height',True)
    def addResizeListener(self,listener):
        self.__listener.append(weakref.ref(listener))
    def _emitResizeEvent(self):
        for l in self.__listener:
            if l() is not None:
                l().OnCanvasResized()
            else:
                self.__listener.remove(l)

    def OnAxisRangeChanged(self):
        self.setSizeByArray([self.__wmode,self.__wvalue,self.__waxis1,self.__waxis2],'Width')
        self.setSizeByArray([self.__hmode,self.__hvalue,self.__haxis1,self.__haxis2],'Height')
class ResizeBox(QGroupBox):
    class _AreaBox(QGroupBox):
        def __init__(self,title,canvas,axis):
            super().__init__(title)
            self._axis=axis
            self.canvas=canvas
            self._initlayout(canvas)
            self.__loadstate()
        def setPartner(self,partner):
            self._partner=weakref.ref(partner)
        def _initlayout(self,canvas):
            layout=QVBoxLayout()

            self.cw=QComboBox()
            self.cw.addItems(['Auto','Absolute','Per Unit','Aspect','Plan'])
            self.cw.activated.connect(self.__ModeChanged)
            layout.addWidget(self.cw)

            tmp=QHBoxLayout()
            self.spin1 = QDoubleSpinBox()
            self.spin1.valueChanged.connect(self.__Changed)
            self.spin1.setDecimals(5)
            self.lab1=QLabel(' * Height')
            tmp.addWidget(self.spin1)
            tmp.addWidget(self.lab1)
            layout.addLayout(tmp)

            tmp=QHBoxLayout()
            self.lab2_1=QLabel('*')
            self.lab2_2=QLabel('Range')
            self.combo2=AxisSelectionWidget(canvas)
            self.combo2.activated.connect(self.__Changed)
            tmp.addWidget(self.lab2_1)
            tmp.addWidget(self.combo2)
            tmp.addWidget(self.lab2_2)
            layout.addLayout(tmp)

            tmp=QHBoxLayout()
            self.lab3_1=QLabel('/')
            self.lab3_2=QLabel('Range')
            self.combo3=AxisSelectionWidget(canvas)
            self.combo3.activated.connect(self.__Changed)
            tmp.addWidget(self.lab3_1)
            tmp.addWidget(self.combo3)
            tmp.addWidget(self.lab3_2)
            layout.addLayout(tmp)

            self.setLayout(layout)
        def __loadstate(self):
            self.__loadflg=True
            lis1=['Auto','Absolute','Per Unit','Aspect','Plan']
            if self._axis==0:
                param=self.canvas.getSizeParams('Width')
            else:
                param=self.canvas.getSizeParams('Height')
            self.cw.setCurrentIndex(lis1.index(param[0]))
            self.spin1.setValue(param[1])
            lis2=self.canvas.axisList()
            self.combo2.setCurrentIndex(lis2.index(param[2]))
            self.combo3.setCurrentIndex(lis2.index(param[3]))
            self._setLook(param[0])
            self.__loadflg=False
        def __ModeChanged(self):
            if self.__loadflg:
                return
            self.__loadflg=True
            type=self.cw.currentText()
            size=self.canvas.getSize()
            if type=='Absolute':
                if self._axis==0:
                    self.spin1.setValue(size[0])
                else:
                    self.spin1.setValue(size[1])
            if type=='Aspect':
                if self._axis==0:
                    self.spin1.setValue(size[0]/size[1])
                else:
                    self.spin1.setValue(size[1]/size[0])
            if type=='Per Unit':
                if self._axis==0:
                    self.combo2.setCurrentIndex(self.canvas.axisList().index('Bottom'))
                    ran=self.canvas.getAxisRange('Bottom')
                    self.spin1.setValue(size[0]/abs(ran[1]-ran[0]))
                else:
                    self.combo2.setCurrentIndex(self.canvas.axisList().index('Left'))
                    ran=self.canvas.getAxisRange('Left')
                    self.spin1.setValue(size[1]/abs(ran[1]-ran[0]))
            if type=='Plan':
                if self._axis==0:
                    self.combo2.setCurrentIndex(self.canvas.axisList().index('Bottom'))
                    self.combo3.setCurrentIndex(self.canvas.axisList().index('Left'))
                    ran_l=self.canvas.getAxisRange('Left')
                    ran_b=self.canvas.getAxisRange('Bottom')
                    self.spin1.setValue(size[0]/size[1]*abs(ran_l[1]-ran_l[0])/abs(ran_b[1]-ran_b[0]))
                else:
                    self.combo2.setCurrentIndex(self.canvas.axisList().index('Left'))
                    self.combo3.setCurrentIndex(self.canvas.axisList().index('Bottom'))
                    ran_l=self.canvas.getAxisRange('Left')
                    ran_b=self.canvas.getAxisRange('Bottom')
                    self.spin1.setValue(size[1]/size[0]*abs(ran_b[1]-ran_b[0])/abs(ran_l[1]-ran_l[0]))
            self.__loadflg=False
            self.__Changed()
        def __Changed(self):
            if self.__loadflg:
                return
            type=self.cw.currentText()
            self._setPartnerComboBox(type)
            self._setLook(type)
            val=self.spin1.value()
            axis1=self.combo2.currentText()
            axis2=self.combo3.currentText()
            if self._axis==0:
                self.canvas.setSizeByArray([type,val,axis1,axis2],'Width')
            else:
                self.canvas.setSizeByArray([type,val,axis1,axis2],'Height')

        def _setPartnerComboBox(self,type):
            part=self._partner()
            val=part.cw.currentIndex()
            part.cw.clear()
            if type in ['Auto','Absolute','Per Unit']:
                part.cw.addItems(['Auto','Absolute','Per Unit','Aspect','Plan'])
            else:
                part.cw.addItems(['Auto','Absolute','Per Unit'])
            part.cw.setCurrentIndex(val)
        def _setLook(self,type):
            if type=='Auto':
                self.spin1.hide()
                self.lab1.setText(' ')
                self._show(2,False)
                self._show(3,False)
            elif type=='Absolute':
                self.spin1.show()
                self.lab1.setText('cm')
                self._show(2,False)
                self._show(3,False)
            elif type=='Per Unit':
                self.spin1.show()
                self.lab1.setText('')
                self._show(2,True)
                self._show(3,False)
            elif type=='Aspect':
                self.spin1.show()
                if self._axis==0:
                    self.lab1.setText('*Height')
                else:
                    self.lab1.setText('*Width')
                self._show(2,False)
                self._show(3,False)
            elif type=='Plan':
                self.spin1.show()
                if self._axis==0:
                    self.lab1.setText('*Height')
                else:
                    self.lab1.setText('*Width')
                self._show(2,True)
                self._show(3,True)
        def _show(self,n,b,text='Range'):
            if n==2:
                if b:
                    self.lab2_1.setText('*')
                    self.lab2_2.setText(text)
                    self.combo2.show()
                else:
                    self.lab2_1.setText(' ')
                    self.lab2_2.setText(' ')
                    self.combo2.hide()
            if n==3:
                if b:
                    self.lab3_1.setText('/')
                    self.lab3_2.setText(text)
                    self.combo3.show()
                else:
                    self.lab3_1.setText(' ')
                    self.lab3_2.setText(' ')
                    self.combo3.hide()

    def __init__(self,canvas):
        super().__init__("Graph Size")
        self.canvas=canvas
        layout_h=QHBoxLayout(self)
        gw=self._AreaBox('Width',canvas,0)
        gh=self._AreaBox('Height',canvas,1)
        gw.setPartner(gh)
        gh.setPartner(gw)
        layout_h.addWidget(gw)
        layout_h.addWidget(gh)
        self.setLayout(layout_h)

class AreaSettingCanvas(ResizableCanvas):
    pass
