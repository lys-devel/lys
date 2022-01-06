from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from lys import *
from .AreaSettings import *

from .AnnotationData import _PyqtgraphLineAnnotation, _PyqtgraphInfiniteLineAnnotation, _PyqtgraphRectAnnotation, _PyqtgraphRegionAnnotation, _PyqtgraphCrossAnnotation


class _PyqtgraphAnnotation(CanvasAnnotation):
    def _addLineAnnotation(self, pos, axis):
        return _PyqtgraphLineAnnotation(self.canvas(), pos, axis)

    def _addInfiniteLineAnnotation(self, pos, type, axis):
        return _PyqtgraphInfiniteLineAnnotation(self.canvas(), pos, type, axis)

    def _addRectAnnotation(self, *args, **kwargs):
        return _PyqtgraphRectAnnotation(self.canvas(), *args, **kwargs)

    def _addRegionAnnotation(self, *args, **kwargs):
        return _PyqtgraphRegionAnnotation(self.canvas(), *args, **kwargs)

    def _addCrossAnnotation(self, *args, **kwargs):
        return _PyqtgraphCrossAnnotation(self.canvas(), *args, **kwargs)


class AnnotationSettingCanvas(AreaSettingCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self._annot = _PyqtgraphAnnotation(self)

    def __getattr__(self, key):
        if "_annot" in self.__dict__:
            if hasattr(self._annot, key):
                return getattr(self._annot, key)
        return super().__getattr__(key)
