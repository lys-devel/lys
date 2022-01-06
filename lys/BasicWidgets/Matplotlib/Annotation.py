from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib.patches import BoxStyle


from lys import *
from .AreaSettings import *
from ..CanvasInterface import CanvasAnnotation

from .AnnotationData import _MatplotlibLineAnnotation, _MatplotlibTextAnnotation


class _MatplotlibAnnotation(CanvasAnnotation):
    def _addLineAnnotation(self, pos, axis):
        return _MatplotlibLineAnnotation(self.canvas(), pos, axis)

    def _addInfiniteLineAnnotation(self, pos, type, axis):
        raise NotImplementedError(str(type(self)) + " does not support infinite line annotation.")

    def _addRectAnnotation(self, *args, **kwargs):
        raise NotImplementedError(str(type(self)) + " does not support rect annotation.")

    def _addRgionAnnotation(self, *args, **kwargs):
        raise NotImplementedError(str(type(self)) + " does not support region annotation.")

    def _addCrossAnnotation(self, *args, **kwargs):
        raise NotImplementedError(str(type(self)) + " does not support crossannotation.")

    def _addTextAnnotation(self, text, pos, axis):
        raise _MatplotlibTextAnnotation(self.canvas(), text, pos, axis)


class AnnotationSettingCanvas(AreaSettingCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.addCanvasPart(_MatplotlibAnnotation(self))
