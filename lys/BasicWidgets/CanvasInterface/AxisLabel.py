import warnings
from lys.errors import NotImplementedWarning
from .SaveCanvas import CanvasPart, saveCanvas


class CanvasAxisLabel(CanvasPart):
    """
    Interface to access axis label of canvas. 
    All methods in this interface can be accessed from :class:`CanvasBase` instance.
    """

    def __init__(self, canvas):
        super().__init__(canvas)
        # canvas.saveCanvas.connect(self._save)
        # canvas.loadCanvas.connect(self._load)
        self.__initialize()
