#!/usr/bin/env python
from PyQt5.QtGui import *
from matplotlib.axis import XAxis, YAxis
from matplotlib.lines import Line2D
from matplotlib.image import AxesImage
from matplotlib.text import Text
from .AnnotGUICanvas import *


class AnchorData(object):
    def __init__(self, obj, obj2, idn, target):
        self.obj = obj
        self.obj2 = obj2
        self.id = idn
        self.target = target


class PicableCanvas(AnnotGUICanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi)
        self.mpl_connect('pick_event', self.OnPick)
        self.__pick = False
        self._resetSelection()

    def _resetSelection(self):
        self.selLine = None
        self.selImage = None
        self.selAxis = None
        self.selAnnot = None

    def OnMouseUp(self, event):
        super().OnMouseUp(event)
        self._resetSelection()
        self.__pick = False

    def OnMouseDown(self, event):
        super().OnMouseDown(event)
        if not self.__pick:
            self._resetSelection()
        self.__pick = False

    def OnPick(self, event):
        self.__pick = True
        if isinstance(event.artist, Text):
            self.selAnnot = event.artist
        elif isinstance(event.artist, XAxis) or isinstance(event.artist, YAxis):
            self.selAxis = event.artist
        elif isinstance(event.artist, Line2D):
            if event.artist.get_zorder() < 0:
                self.selLine = event.artist
        elif isinstance(event.artist, AxesImage):
            if event.artist.get_zorder() < 0:
                self.selImage = event.artist

    def getPickedLine(self):
        return self.selLine

    def getPickedImage(self):
        return self.selImage

    def getPickedAxis(self):
        return self.selAxis

    def getPickedAnnotation(self):
        return self.selAnnot


class AnchorSettingCanvas(PicableCanvas):
    pass
