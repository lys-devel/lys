#!/usr/bin/env python
import sys
import os
from PyQt5.QtGui import *
from .Fitting.FittingWidget import FittingWidget
from .Fitting.LineProfile import LineProfileWidget
from ExtendAnalysis.widgets import LysSubWindow


class FittingWindow(LysSubWindow):
    def __init__(self, parent, wavelist, canvas=None):
        super().__init__()
        self._initlayout(wavelist, canvas)
        self.adjustSize()
        self.updateGeometry()
        self.attach(parent)
        self.show()
        self.attachTo()

    def _initlayout(self, wavelist, canvas):
        self.setWindowTitle("Fitting Window")
        w = FittingWidget(wavelist, canvas)
        self.setWidget(w)


class LineProfileWindow(LysSubWindow):
    def __init__(self, parent, wavelist, canvas=None):
        super().__init__()
        self._initlayout(wavelist, canvas)
        self.adjustSize()
        self.updateGeometry()
        self.attach(parent)
        self.show()
        self.attachTo()

    def _initlayout(self, wavelist, canvas):
        self.setWindowTitle("Line Profile Window")
        w = LineProfileWidget(wavelist, canvas)
        self.setWidget(w)
