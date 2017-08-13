#!/usr/bin/env python
import random, weakref, gc, sys, os
from collections import namedtuple
from ColorWidgets import *
import numpy as np
from enum import Enum
from ExtendType import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure, SubplotParams
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.widgets import RectangleSelector
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import lines, markers, ticker
class Axis(Enum):
    BottomLeft=1
    TopLeft=2
    BottomRight=3
    TopRight=4

class SizeAdjustableWindow(QMdiSubWindow):
    def __init__(self):
        super().__init__()
        #Mode
        #0 : Auto
        #1 : heightForWidth
        #2 : widthForHeight
        self.__mode=0
        self.__aspect=0
        self.setWidth(0)
        self.setHeight(0)
    def setWidth(self,val):
        if self.__mode==2:
            self.__mode=0
        if val==0:
            self.setMinimumWidth(85)
            self.setMaximumWidth(100000)
        else:
            self.setMinimumWidth(val)
            self.setMaximumWidth(val)
    def setHeight(self,val):
        if self.__mode==1:
            self.__mode=0
        if val==0:
            self.setMinimumHeight(85)
            self.setMaximumHeight(100000)
        else:
            self.setMinimumHeight(val)
            self.setMaximumHeight(val)
    def setHeightForWidth(self,val):
        self.__mode=1
        self.__aspect=val
    def setWidthForHeight(self,val):
        self.__mode=2
        self.__aspect=val
    def resizeEvent(self,event):
        self._resizeEvent(event.size())
        return super().resizeEvent(event)
    def _resizeEvent(self,size):
        if self.__mode==1:
            self.setMinimumHeight(size.width()*self.__aspect)
            self.setMaximumHeight(size.width()*self.__aspect)
        elif self.__mode==2:
            self.setMinimumWidth(size.height()*self.__aspect)
            self.setMaximumWidth(size.height()*self.__aspect)
class AttachableWindow(SizeAdjustableWindow):
    resized=pyqtSignal()
    moved=pyqtSignal()
    closed=pyqtSignal()
    def __init__(self):
        super().__init__()
    def resizeEvent(self,event):
        self.resized.emit()
        return super().resizeEvent(event)
    def moveEvent(self,event):
        self.moved.emit()
        return super().moveEvent(event)
    def closeEvent(self,event):
        self.closed.emit()
        return super().closeEvent(event)
class AutoSavedWindow(AttachableWindow, AutoSaved):
    __list=[]
    mdimain=None
    @classmethod
    def CloseAllWindows(cls):
        for g in cls.__list:
            g.close()
    @classmethod
    def _AddWindow(cls,win):
        cls.__list.append(win)
    @classmethod
    def _RemoveWindow(cls,win):
        cls.__list.remove(win)
    @classmethod
    def _Contains(cls,win):
        return win in cls.__list
    @classmethod
    def DisconnectedWindows(cls):
        res=[]
        for g in cls.__list:
            if not g.IsConnected():
                res.append(g)
        return res
    @classmethod
    def AllWindows(cls):
        return cls.__list

    def __new__(cls, file=None,title=None):
        return AutoSaved.__new__(cls,file,AttachableWindow)
    def __init__(self, file=None, title=None):
        AutoSaved.__init__(self,file,AttachableWindow)
        AutoSavedWindow._AddWindow(self)
        if title is not None:
            self.setWindowTitle(title)
        self.updateGeometry()
        self.show()
    def __setattr__(self,key,value):
        object.__setattr__(self,key,value)
    def closeEvent(self,event):
        if self.IsConnected() or self.isHidden():
            self.Save()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("This window is not saved. Do you really want to close it?")
            msg.setWindowTitle("Caution")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ok = msg.exec_()
            if ok==QMessageBox.Cancel:
                event.ignore()
                return
        AutoSavedWindow._RemoveWindow(self)
        self.Disconnect()
        event.accept()
        return AttachableWindow.closeEvent(self,event)
    def hide(self):
        sys.stderr.write('This window cannot be hidden.\n')
    def show(self):
        if AutoSavedWindow._Contains(self):
            super().show()
        else:
            sys.stderr.write('This window is already closed.\n')

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
        if AutoSavedWindow.mdimain is not None:
            AutoSavedWindow.mdimain.addSubWindow(self)
            self.setWidget(self.canvas)
        else:
            self.setCentralWidget(self.canvas)
    def closeEvent(self,event):
        self.canvas.fig.canvas=None
        super().closeEvent(event)
    def Append(self,wave,axis=Axis.BottomLeft):
        self.canvas.Append(wave,axis)
    def Make_ModifyWindow(self):
        self._mod=ModifyWindow(self.canvas,self)
        if AutoSavedWindow.mdimain is not None:
            AutoSavedWindow.mdimain.addSubWindow(self._mod)
        self._mod.show()
        self._mod.attachTo()
class PreviewWindow(QMainWindow):
    instance=None
    @classmethod
    def CloseAllWindows(cls):
        if not cls.instance is None:
            cls.instance.close()
    def __new__(cls,*list):
        if cls.instance is None:
            return QMainWindow.__new__(cls)
        else:
            return cls.instance

    def __init__(self,*list):
        if PreviewWindow.instance is None:
            PreviewWindow.instance=self
            QMainWindow.__init__(self)
            self.setWindowTitle("Preview Window")
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.updateGeometry()
            self.left=ExtendCanvas()
            self.main=ExtendCanvas()
            self.bottom=ExtendCanvas()
            self._setLayout(2)
        else:
            self.main.Clear()
            self.left.Clear()
            self.bottom.Clear()
        for l in list:
            self.main.Append(l)
        self.show()

    def _setLayout(self,mode):
        if mode==2:
            layout=QGridLayout()
            layout.setSpacing(0)
            layout.addWidget(self.left,0,0)
            layout.addWidget(self.main,0,1)
            layout.addWidget(self.bottom,1,1)
            wid=QWidget(self)
            wid.setLayout(layout)
            self.setCentralWidget(wid)
        elif mode==1:
            self.setCentralWidget(self.main)

from GraphSettings.Annotation import *
class ExtendCanvas(AnnotationSettingCanvas):
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

    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)

    def buildContextMenu( self, qPoint ):
        menu = QMenu( self )
        if self.IsRangeSelected():
            menulabels = ['Expand', 'Horizontal Expand', 'Vertical Expand', 'Shrink', 'Horizontal Shrink', 'Vertical Shrink']
        else:
            menulabels = ['Modify Graph','Auto scale axes','Add annotation']
        actionlist = []
        for label in menulabels:
            actionlist.append( menu.addAction( label ) )

        action = menu.exec_( self.mapToGlobal( qPoint ) )
        if not action is None:
            if action.text() in ['Expand', 'Horizontal Expand', 'Vertical Expand', 'Shrink', 'Horizontal Shrink', 'Vertical Shrink']:
                self.__ExpandAndShrink(action.text(),self.axes)
                self.__ExpandAndShrink(action.text(),self.axes_tx,False,True)
                self.__ExpandAndShrink(action.text(),self.axes_ty,True,False)
                self.__ExpandAndShrink(action.text(),self.axes_txy)
                self.ClearSelectedRange()
                self.draw()
            if action.text() in ['Auto scale axes']:
                self.axes.autoscale()
                if not self.axes_tx == None:
                    self.axes_tx.autoscale()
                if not self.axes_ty == None:
                    self.axes_ty.autoscale()
                if not self.axes_txy == None:
                    self.axes_txy.autoscale()
                self.draw()
            if action.text() in ['Modify Graph']:
                print('dummy: please make modification graph')
            if action.text()=='Add annotation':
                self.addAnnotation('test')
    def __ExpandAndShrink(self, mode,ax,flg_x=True,flg_y=True):
        if ax==None:
            return -1
        pos=self.__GlobalToAxis(self.rect_pos_start[0],self.rect_pos_start[1],ax)
        pos2=self.__GlobalToAxis(self.rect_pos_end[0],self.rect_pos_end[1],ax)
        width=pos2[0]-pos[0]
        height=pos2[1]-pos[1]
        xlim=ax.get_xlim()
        ylim=ax.get_ylim()

        if flg_x is True:
            if mode in ['Horizontal Expand', 'Expand']:
                minVal=min(pos[0], pos[0]+width)
                maxVal=max(pos[0], pos[0]+width)
                ax.set_xlim([minVal,maxVal])
            if mode in ['Shrink','Horizontal Shrink']:
                ratio=abs((xlim[1]-xlim[0])/width)
                a=min(pos[0], pos[0]+width)
                b=max(pos[0], pos[0]+width)
                minVal=xlim[0]-ratio*(a-xlim[0])
                maxVal=xlim[1]+ratio*(xlim[1]-b)
                ax.set_xlim([minVal,maxVal])
        if flg_y is True:
            if mode in ['Vertical Expand', 'Expand']:
                minVal=min(pos[1], pos[1]+height)
                maxVal=max(pos[1], pos[1]+height)
                ax.set_ylim([minVal,maxVal])

            if mode in ['Shrink','Vertical Shrink']:
                ratio=abs((ylim[1]-ylim[0])/height)
                a=min(pos[1], pos[1]+height)
                b=max(pos[1], pos[1]+height)
                minVal=ylim[0]-ratio*(a-ylim[0])
                maxVal=ylim[1]+ratio*(ylim[1]-b)
                ax.set_ylim([minVal,maxVal])

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_G and self.parentWidget() is not None:
            self.parentWidget().Make_ModifyWindow()

class ModifyWindow(QMdiSubWindow):
    def __init__(self, canvas, parent=None):
        QMainWindow.__init__(self)
        self._initlayout(canvas,parent)
        self.updateGeometry()
        self.show()
        self.canvas=canvas
        self._parent=parent
        if parent is not None:
            self._parent.moved.connect(self.attachTo)
            self._parent.resized.connect(self.attachTo)
            self._parent.closed.connect(self.close)
    def closeEvent(self,event):
        if self._parent is not None:
            self._parent._mod=None
        super().closeEvent(event)
    def attachTo(self):
        if self._parent is not None:
            pos=self._parent.pos()
            frm=self._parent.frameGeometry()
            self.move(QPoint(pos.x()+frm.width(),pos.y()))

    def _initlayout(self,canvas,win):
        self.setWindowTitle("Modify Window")
        self._tab=QTabWidget()
        self._tab.addTab(_AreaTab(canvas),"Area")
        self._tab.addTab(_AxisTab(canvas),"Axis")
        self._tab.addTab(_LineTab(canvas),"Lines")
        self._tab.addTab(_ImageTab(canvas),"Images")
        self._tab.addTab(_AnnotationTab(canvas),"Annot.")
        self.setWidget(self._tab)

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
