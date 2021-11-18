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
from .Margin import MarginBase


class TemporaryCanvasBase(ImageColorAdjustableCanvasBase):
    saveCanvas = pyqtSignal(dict)
    loadCanvas = pyqtSignal(dict)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def SaveAsDictionary(self, dictionary, path):
        super().SaveAsDictionary(dictionary, path)
        self.saveCanvas.emit(dictionary)

    def LoadFromDictionary(self, dictionary, path):
        super().LoadFromDictionary(dictionary, path)
        self.loadCanvas.emit(dictionary)


class AbstractCanvasBase(TemporaryCanvasBase):
    pass
