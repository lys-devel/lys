from .Axes import CanvasAxes, CanvasTicks
from .Area import MarginBase, CanvasSizeBase
from .AxisLabel import CanvasAxisLabel, CanvasTickLabel
from .Data import CanvasData, LineData, ImageData, RGBData, VectorData, ContourData
from .Font import FontInfo, CanvasFont
from .Annotation import CanvasAnnotation

from .SaveCanvas import *

from .Annotation import *
from .TextAnnotation import *
from .LineAnnotation import *
from .RectAnnotation import *
from .RegionAnnotation import *
from .CrosshairAnnotation import *
from .AnnotGUICanvas import *


class TemporaryCanvasBase(DrawableCanvasBase):
    saveCanvas = pyqtSignal(dict)
    loadCanvas = pyqtSignal(dict)
    initCanvas = pyqtSignal()

    def SaveAsDictionary(self, dictionary, path):
        super().SaveAsDictionary(dictionary, path)
        self.saveCanvas.emit(dictionary)

    def LoadFromDictionary(self, dictionary, path):
        super().LoadFromDictionary(dictionary, path)
        self.loadCanvas.emit(dictionary)


class AbstractCanvasBase(TemporaryCanvasBase):
    pass
