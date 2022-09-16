import warnings

from lys.Qt import QtCore
from lys.errors import NotImplementedWarning

from .CanvasBase import CanvasPart, saveCanvas


class CanvasLegend(CanvasPart):
    """
    Abstract base class for Legend. 
    All methods in this interface can be accessed from :class:`CanvasBase` instance.
    """

    def __init__(self, canvas):
        super().__init__(canvas)
        # canvas.saveCanvas.connect(self._save)
        # canvas.loadCanvas.connect(self._load)

    def _save(self, dictionary):
        dictionary['Margin'] = self._margins

    def _load(self, dictionary):
        if 'Margin' in dictionary:
            m = dictionary['Margin']
            self.setMargin(*m)
