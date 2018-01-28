#!/usr/bin/env python
import sys, os
from PyQt5.QtGui import *
from .Fitting.FittingWidget import FittingWidget
from .ExtendType import *

class FittingWindow(ExtendMdiSubWindow):
    def __init__(self, parent, wavelist, canvas=None):
        super().__init__()
        self._initlayout(wavelist,canvas)
        self.adjustSize()
        self.updateGeometry()
        self.show()
        self._parent=parent
        if isinstance(parent,ExtendMdiSubWindow):
            self._parent.moved.connect(self.attachTo)
            self._parent.resized.connect(self.attachTo)
            self._parent.closed.connect(self.close)
        self.attachTo()
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
    def _initlayout(self,wavelist,canvas):
        self.setWindowTitle("Fitting Window")
        w=FittingWidget(wavelist,canvas)
        self.setWidget(w)
