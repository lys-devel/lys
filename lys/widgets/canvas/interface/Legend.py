import warnings

from lys.Qt import QtCore
from lys.errors import NotImplementedWarning

from .CanvasBase import CanvasPart, saveCanvas
from .Font import FontInfo


class CanvasLegend(CanvasPart):
    """
    Abstract base class for Legend.
    All methods in this interface can be accessed from :class:`CanvasBase` instance.
    """

    legendPositionChanged = QtCore.pyqtSignal(tuple)

    def __init__(self, canvas):
        super().__init__(canvas)
        canvas.saveCanvas.connect(self._save)
        canvas.loadCanvas.connect(self._load)
        canvas.initCanvas.connect(self._init)
        self._position = (0, 0)

    def _init(self):
        self.setLegendFont(FontInfo.defaultFont())
        self.setLegendPosition((0.1, 0.8))
        self.setLegendFrameVisible(True)

    @ saveCanvas
    def setLegendFont(self, fname, size=10, color="black"):
        """
        Set the font of the legend.

        Args:
            fname(str): The name of the font.
            size(int): The size of the font.
            color(str): The color of the font such as #111111.
        """
        if isinstance(fname, FontInfo):
            font = fname
        else:
            font = FontInfo(fname, size, color)
        self._setLegendFont(font)
        self._font = font.toDict()

    def getLegendFont(self):
        """
        Get the font of the legend.

        Return:
            dict: The information of font. See :meth:`setLegendFont`
        """
        return self._font

    @ saveCanvas
    def setLegendPosition(self, position):
        """
        Set the position of the legend.

        Args:
            position(tuple): The position of the legend in the form of (x,y)
        """
        position = tuple(position)
        self._setLegendPosition(position)
        self._position = position
        self.legendPositionChanged.emit(self._position)

    def getLegendPosition(self):
        """
        Get the font of the legend.

        Return:
            tuple: The position of the legend.
        """
        return self._position

    @ saveCanvas
    def setLegendFrameVisible(self, visible):
        """
        Show/hide the frame of the legend.

        Args:
            visible(bool): The visibility of the frame
        """
        self._setLegendFrameVisible(visible)
        self._frameon = visible

    def getLegendFrameVisible(self):
        """
        Get the visibility of the frame

        Return:
            bool: The visibility of the frame.
        """
        return self._frameon

    def _save(self, dictionary):
        dictionary['Legend'] = {"font": self._font, "position": self._position, "frameon": self._frameon}

    def _load(self, dictionary):
        if 'Legend' in dictionary:
            d = dictionary['Legend']
            if "font" in d:
                self.setLegendFont(FontInfo.fromDict(d["font"]))
            if "position" in d:
                self.setLegendPosition(d["position"])
            if "frameon" in d:
                self.setLegendFrameVisible(d["frameon"])

    def _setLegendFont(self, name, size, color):
        warnings.warn(str(type(self)) + " does not implement _setLegendFont(name, size, color) method.", NotImplementedWarning)

    def _setLegendPosition(self, position):
        warnings.warn(str(type(self)) + " does not implement _setLegendPosition(position) method.", NotImplementedWarning)
