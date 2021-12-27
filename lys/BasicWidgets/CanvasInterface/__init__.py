from .SaveCanvas import *
from .CanvasBase import *
from .LineSettings import *
from .ImageSettings import *
from .Annotation import *
from .TextAnnotation import *
from .LineAnnotation import *
from .RectAnnotation import *
from .RegionAnnotation import *
from .CrosshairAnnotation import *
from .AnnotGUICanvas import *
from .RGBSettings import *
from .Axes import CanvasAxes, CanvasTicks
from .Area import MarginBase, CanvasSizeBase
from .AxisLabel import CanvasAxisLabel, CanvasTickLabel
from .Font import FontInfo, CanvasFont
from .WaveData import LineData, ImageData, VectorData, RGBData, ContourData


class TemporaryCanvasBase(ImageColorAdjustableCanvasBase):
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
