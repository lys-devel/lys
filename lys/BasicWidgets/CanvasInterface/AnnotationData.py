import warnings
from lys.errors import NotImplementedWarning

from .SaveCanvas import CanvasPart, saveCanvas


class _AnnotationData(CanvasPart):
    def __init__(self, canvas, name, axis):
        super().__init__(canvas)
        self._name = name
        self._appearance = {}
        self._axis = axis

    def getName(self):
        return self._name

    def getAxis(self):
        return self._axis

    @saveCanvas
    def loadAppearance(self, appearance):
        self._loadAppearance(appearance)

    def saveAppearance(self):
        return dict(self._appearance)

    def _loadAppearance(self, appearance):
        warnings.warn(str(type(self)) + " does not implement _loadAppearance(appearance) method.", NotImplementedWarning)
