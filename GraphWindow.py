#!/usr/bin/env python
import random, sys, os
from enum import Enum
from PyQt5.QtGui import *

from .ExtendType import *
from .Widgets.ExtendCanvas import *
from .Widgets.ExtendTable import *
from .ModifyWindow import ModifyWindow

class Graph(AutoSavedWindow):
    @classmethod
    def active(cls,n=0):
        list=cls.mdimain.subWindowList(order=QMdiArea.ActivationHistoryOrder)
        m=0
        for l in reversed(list):
            if isinstance(l,Graph):
                if m==n:
                    return l
                else:
                    m+=1
    def _save(self,file):
        d={}
        self.canvas.SaveAsDictionary(d,os.path.dirname(file))
        d['Graph']={}
        d['Graph']['Position_x']=self.pos().x()
        d['Graph']['Position_y']=self.pos().y()
        with open(file,'w') as f:
            f.write(str(d))
    def _load(self,file):
        with open(file,'r') as f:
            d=eval(f.read())
        self.move(d['Graph']['Position_x'],d['Graph']['Position_y'])
        self.canvas.EnableDraw(False)
        self.canvas.LoadFromDictionary(d,os.path.dirname(file))
        self.canvas.EnableDraw(True)
        self.canvas.draw()
    def _init(self):
        self.canvas=ExtendCanvas()
        self.resize(200,200)
        self.canvas.setModificationFunction(self.Make_ModifyWindow)
        self.setWidget(self.canvas)
    def closeEvent(self,event):
        self.canvas.fig.canvas=None
        super().closeEvent(event)
    def Append(self,wave,axis=Axis.BottomLeft):
        self.canvas.Append(wave,axis)
    def Make_ModifyWindow(self,canvas,tab='Area'):
        mod=ModifyWindow(canvas,self)
        mod.selectTab(tab)
class PreviewWindow(ExtendMdiSubWindow):
    instance=None
    def __new__(cls,list):
        if cls.__checkInstance():
            return cls.instance()
        return ExtendMdiSubWindow.__new__(cls)
    @classmethod
    def __checkInstance(cls):
        if cls.instance is not None:
            if cls.instance() is not None:
                return True
        return False
    def __init__(self,list):
        if self.__checkInstance():
            self.main.Clear()
            self.left.Clear()
            self.bottom.Clear()
        else:
            PreviewWindow.instance=weakref.ref(self)
            super().__init__()
            self.setWindowTitle("Preview Window")
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.resize(500,500)
            self.updateGeometry()
            self.__initcanvas()
            self.__initlayout()
        n=1
        if hasattr(list, '__iter__'):
            lists=list
        else:
            lists=[list]
        for l in lists:
            self.main.Append(l)
            n=max(n,l.data.ndim)
        self.dim=n
        self._setLayout(n)
        self.axis_c()
        self.show()
    def __initcanvas(self):
        self.left=ExtendCanvas()
        self.left.addAxisRangeChangeListener(self.axis_l)
        self.main=ExtendCanvas()
        self.main.addAxisRangeChangeListener(self.axis_c)
        self.main.addAnchorChangedListener(self.OnAnchorChanged)
        self.bottom=ExtendCanvas()
        self.bottom.addAxisRangeChangeListener(self.axis_b)
        self.axisflg=False
    def __initlayout(self):
        layout=QGridLayout()
        layout.setSpacing(0)
        layout.addWidget(self.left,0,0)
        layout.addWidget(self.main,0,1)
        layout.addWidget(self.bottom,1,1)

        layout.setRowStretch(0, 6)
        layout.setRowStretch(1, 4)
        layout.setColumnStretch(0, 4)
        layout.setColumnStretch(1, 6)
        self.gl=layout
        wid=QWidget(self)
        wid.setLayout(layout)
        self.setWidget(wid)
    def _setLayout(self,mode):
        if mode==2:
            self.gl.setRowStretch(0, 6)
            self.gl.setRowStretch(1, 4)
            self.gl.setColumnStretch(0, 4)
            self.gl.setColumnStretch(1, 6)
            self.left.show()
            self.bottom.show()
        elif mode==1:
            self.gl.setRowStretch(0, 6)
            self.gl.setRowStretch(1, 0)
            self.gl.setColumnStretch(0, 0)
            self.gl.setColumnStretch(1, 6)
            self.left.hide()
            self.bottom.hide()
    def axis_l(self):
        if self.axisflg:
            return
        self.axisflg=True
        range=self.left.getAxisRange('Left')
        self.main.setAxisRange(range,'Left')
        self.axisflg=False
    def axis_b(self):
        if self.axisflg:
            return
        self.axisflg=True
        range=self.bottom.getAxisRange('Bottom')
        self.main.setAxisRange(range,'Bottom')
        self.axisflg=False
    def axis_c(self):
        if self.axisflg:
            return
        self.axisflg=True
        range=self.main.getAxisRange('Left')
        self.left.setAxisRange(range,'Left')
        range=self.main.getAxisRange('Bottom')
        self.bottom.setAxisRange(range,'Bottom')
        self.axisflg=False
    def __posToPoint(self,wave,pos):
        x0=wave.x[0]
        x1=wave.x[len(wave.x)-1]
        y0=wave.y[0]
        y1=wave.y[len(wave.y)-1]
        wx=(x1-x0)/wave.data.shape[0]
        wy=(y1-y0)/wave.data.shape[1]
        return (round((pos[0]-x0-wx/2)/wx),round((pos[1]-y0-wy/2)/wy))
    def OnAnchorChanged(self):
        self.left.Clear()
        self.bottom.Clear()
        for i in [1,2,3]:
            res=self.main.getAnchorInfo(i)
            if res is None:
                continue
            w=res[0]
            if w is None:
                continue
            if w.wave.data.ndim==2:
                p=self.__posToPoint(w.wave,res[1])
                slicex=w.wave.slice((0,p[1]),(w.wave.data.shape[0],p[1]),axis='x')
                slicey=w.wave.slice((p[0],0),(p[0],w.wave.data.shape[1]),axis='y')
                data=slicey.data
                slicey.data=slicey.x
                slicey.x=data
                id1=self.left.Append(slicey)
                id2=self.bottom.Append(slicex)
                self.left.setDataColor(self.main.getAnchorColor(i),id1)
                self.bottom.setDataColor(self.main.getAnchorColor(i),id2)
class Table(ExtendMdiSubWindow):
    def __init__(self,wave):
        super().__init__()
        self.setWindowTitle("Table Window")
        self.resize(400,400)
        self._etable=ExtendTable(wave)
        self.setWidget(self._etable)
        self.show()
