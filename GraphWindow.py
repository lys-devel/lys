#!/usr/bin/env python
import random, sys, os
from enum import Enum
from PyQt5.QtGui import *

from .ExtendType import *
from .Widgets.ExtendCanvas import *

class Graph(AutoSavedWindow):
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
        self.canvas.LoadFromDictionary(d,os.path.dirname(file))
        self.canvas.draw()
    def _init(self):
        self._mod=None
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
        self._mod=ModifyWindow(canvas,self)
        self._mod.selectTab(tab)
class PreviewWindow(ExtendMdiSubWindow):
    instance=None
    def __new__(cls,list):
        if cls.instance is None:
            return QMainWindow.__new__(cls)
        else:
            return cls.instance
    def __init__(self,list):
        if PreviewWindow.instance is None:
            PreviewWindow.instance=self
            super().__init__()
            self.setWindowTitle("Preview Window")
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.resize(500,500)
            self.updateGeometry()
            self.__initcanvas()
            self.__initlayout()
        else:
            self.main.Clear()
            self.left.Clear()
            self.bottom.Clear()
        n=1
        for l in list:
            self.main.Append(l)
            n=max(n,l.data.ndim)
        self.dim=n
        self._setLayout(n)
        self.axis_c()
        self.show()
    def __initcanvas(self):
        self.left=ExtendCanvas()
        self.left.setModificationFunction(self.Make_ModifyWindow)
        self.left.addAxisRangeChangeListener(self.axis_l)

        self.main=ExtendCanvas()
        self.main.setModificationFunction(self.Make_ModifyWindow)
        self.main.addAxisRangeChangeListener(self.axis_c)
        self.main.addAnchorChangedListener(self.OnAnchorChanged)

        self.bottom=ExtendCanvas()
        self.bottom.setModificationFunction(self.Make_ModifyWindow)
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
    def Make_ModifyWindow(self,canvas,tab='Axis'):
        self._mod=ModifyWindow(canvas,self,showArea=False)
        self._mod.selectTab(tab)
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

class ModifyWindow(ExtendMdiSubWindow):
    instance=None
    def __init__(self, canvas, parent=None, showArea=True):
        super().__init__()
        if ModifyWindow.instance is not None:
            ModifyWindow.instance.close()
        self._initlayout(canvas,parent,showArea)
        self.adjustSize()
        self.updateGeometry()
        self.show()
        self.canvas=canvas
        self._parent=parent
        if isinstance(parent,ExtendMdiSubWindow):
            self._parent.moved.connect(self.attachTo)
            self._parent.resized.connect(self.attachTo)
            self._parent.closed.connect(self.close)
        self.attachTo()
        ModifyWindow.instance=self
    def closeEvent(self,event):
        if self._parent is not None:
            self._parent._mod=None
            self._parent.moved.disconnect(self.attachTo)
            self._parent.resized.disconnect(self.attachTo)
            self._parent.closed.disconnect(self.close)
        super().closeEvent(event)
    def attachTo(self):
        if self._parent is not None:
            pos=self._parent.pos()
            frm=self._parent.frameGeometry()
            self.move(QPoint(pos.x()+frm.width(),pos.y()))
    def _initlayout(self,canvas,win,showArea):
        self.__list=[]
        self.setWindowTitle("Modify Window")
        self._tab=QTabWidget()
        if showArea:
            self._tab.addTab(_AreaTab(canvas),"Area")
            self.__list.append('Area')
        self._tab.addTab(_AxisTab(canvas),"Axis")
        self._tab.addTab(_LineTab(canvas),"Lines")
        self._tab.addTab(_ImageTab(canvas),"Images")
        self._tab.addTab(_AnnotationTab(canvas),"Annot.")
        self.__list.append('Axis')
        self.__list.append('Lines')
        self.__list.append('Images')
        self.__list.append('Annot.')
        self.setWidget(self._tab)
    def selectTab(self,tab):
        self._tab.setCurrentIndex(self.__list.index(tab))

class _AreaTab(QWidget):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        self._initlayout(canvas)

    def _initlayout(self,canvas):
        self._size=ResizeBox(canvas)
        self._margin=MarginAdjustBox(canvas)
        self.layout=QVBoxLayout(self)
        self.layout.addWidget(self._size)
        self.layout.addWidget(self._margin)
        self.setLayout(self.layout)
class _AxisTab(QWidget):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        self._initlayout(canvas)
    def _initlayout(self,canvas):
        layout=QVBoxLayout(self)
        layout.addWidget(AxisSelectionWidget(canvas))
        tab=QTabWidget()
        tab.addTab(AxisAndTickBox(canvas),'Main')
        tab.addTab(AxisAndTickLabelBox(canvas),'Label')
        tab.addTab(AxisFontBox(canvas),'Font')
        layout.addWidget(tab)

        self.setLayout(layout)
class _LineTab(QWidget):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        self._initlayout(canvas)
    def _initlayout(self,canvas):
        layout=QVBoxLayout()
        layout.addWidget(RightClickableSelectionBox(canvas,1))

        tab=QTabWidget()
        tab.addTab(ApperanceBox(canvas),'Appearance')
        tab.addTab(OffsetAdjustBox(canvas,1),'Offset')

        layout.addWidget(tab)
        self.setLayout(layout)
class _ImageTab(QWidget):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        self._initlayout(canvas)
    def _initlayout(self,canvas):
        layout=QVBoxLayout()
        layout.addWidget(RightClickableSelectionBox(canvas,2))
        tab=QTabWidget()
        tab.addTab(ImageColorAdjustBox(canvas),'Color')
        tab.addTab(OffsetAdjustBox(canvas,2),'Offset')
        layout.addWidget(tab)
        self.setLayout(layout)
class _AnnotationTab(QWidget):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        self._initlayout(canvas)
    def _initlayout(self,canvas):
        layout=QVBoxLayout(self)
        tab=QTabWidget()
        tab.addTab(AnnotationBox(canvas),'Text')
        self._test=QPushButton('Legend(test)')
        self._test.clicked.connect(self.test)
        tab.addTab(self._test,'Legend')
        layout.addWidget(tab)
        self.setLayout(layout)
    def test(self):
        a=self.canvas.axes.legend()
        self.canvas.draw()
