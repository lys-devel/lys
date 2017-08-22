#!/usr/bin/env python
import sys, os
from PyQt5.QtGui import *

from .ExtendType import *
from .Widgets.ExtendCanvas import *

class ModifyWindow(ExtendMdiSubWindow):
    instance=None
    def __init__(self, canvas, parent=None, showArea=True):
        super().__init__()
        if ModifyWindow.instance is not None:
            if ModifyWindow.instance() is not None:
                ModifyWindow.instance().close()
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
        ModifyWindow.instance=weakref.ref(self)
    def closeEvent(self,event):
        if self._parent is not None:
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
