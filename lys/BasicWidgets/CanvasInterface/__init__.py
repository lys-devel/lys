from .Axes import CanvasAxes, CanvasTicks
from .Area import MarginBase, CanvasSizeBase
from .AxisLabel import CanvasAxisLabel, CanvasTickLabel
from .Font import FontInfo, CanvasFont
from .WaveData import VectorData, RGBData, ContourData
from .Line import LineData
from .Image import ImageData


from .SaveCanvas import *
from .CanvasBase import *

from .Annotation import *
from .TextAnnotation import *
from .LineAnnotation import *
from .RectAnnotation import *
from .RegionAnnotation import *
from .CrosshairAnnotation import *
from .AnnotGUICanvas import *


class TemporaryCanvasBase(OffsetAdjustableCanvasBase):
    saveCanvas = pyqtSignal(dict)
    loadCanvas = pyqtSignal(dict)

    def SaveAsDictionary(self, dictionary, path):
        super().SaveAsDictionary(dictionary, path)
        self.saveCanvas.emit(dictionary)

    def LoadFromDictionary(self, dictionary, path):
        super().LoadFromDictionary(dictionary, path)
        self.loadCanvas.emit(dictionary)


class AbstractCanvasBase(TemporaryCanvasBase):
    pass
