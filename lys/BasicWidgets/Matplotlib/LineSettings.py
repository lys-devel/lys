#!/usr/bin/env python
import random
import weakref
import gc
import sys
import os
from collections import namedtuple
import numpy as np
from enum import Enum
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure, SubplotParams
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.widgets import RectangleSelector
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import lines, markers

from .CanvasBase import *
from ..CanvasInterface import *


class LineColorAdjustableCanvas(FigureCanvasBase):
    def _setDataColor(self, obj, color):
        obj.set_color(color)

    def _getDataColor(self, obj):
        return obj.get_color()


class LineStyleAdjustableCanvas(LineColorAdjustableCanvas):
    def _getLineDataStyle(self, obj):
        return obj.get_linestyle().replace('-.', 'dashdot').replace('--', 'dashed').replace('-', 'solid').replace(':', 'dotted')

    def _setLineDataStyle(self, obj, style):
        obj.set_linestyle(style)

    def _getLineDataWidth(self, obj):
        return obj.get_linewidth()

    def _setLineDataWidth(self, obj, width):
        obj.set_linewidth(width)


class MarkerStyleAdjustableCanvas(LineStyleAdjustableCanvas):
    def _getMarker(self, obj):
        dummy = lines.Line2D([0, 1], [0, 1])
        return dummy.markers[obj.get_marker()]

    def _getMarkerSize(self, obj):
        return obj.get_markersize()

    def _getMarkerThick(self, obj):
        return obj.get_markeredgewidth()

    def _getMarkerFilling(self, obj):
        return obj.get_fillstyle()

    def _setMarker(self, obj, marker):
        dummy = lines.Line2D([0, 1], [0, 1])
        key = list(dummy.markers.keys())
        val = list(dummy.markers.values())
        if marker in val:
            obj.set_marker(key[val.index(marker)])

    def _setMarkerSize(self, obj, size):
        obj.set_markersize(size)

    def _setMarkerThick(self, obj, thick):
        obj.set_markeredgewidth(thick)

    def _setMarkerFilling(self, obj, filling):
        dummy = lines.Line2D([0, 1], [0, 1])
        if filling in dummy.fillStyles:
            obj.set_fillstyle(filling)

    def getMarkerList(self):
        dummy = lines.Line2D([0, 1], [0, 1])
        return dummy.markers

    def getMarkerFillingList(self):
        dummy = lines.Line2D([0, 1], [0, 1])
        return dummy.fillStyles
