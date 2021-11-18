from LysQt.QtCore import pyqtSignal
from .SaveCanvas import CanvasPart, saveCanvas


class MarginBase(CanvasPart):
    """
    Base class for Margin. 
    Developers should implement a method _setMargin(left, right, bottom, top).
    """

    marginChanged = pyqtSignal()
    """Emitted when margin is changed."""

    def __init__(self, canvas):
        super().__init__(canvas)
        self.setMargin()
        canvas.saveCanvas.connect(self._save)
        canvas.loadCanvas.connect(self._load)

    @saveCanvas
    def setMargin(self, left=0, right=0, bottom=0, top=0):
        """Set margin of canvas. Zero means auto.

        Args:
            left (float): The position of the left edge of the subplots, as a fraction of the figure width.
            right (float): The position of the right edge of the subplots, as a fraction of the figure width.
            bottom (float): The position of the bottom edge of the subplots, as a fraction of the figure height.
            top (float): The position of the top edge of the subplots, as a fraction of the figure height.

        Examples:

            from lys import display
            g = display([1,2,3])
            g.canvas.margin.setMargin(0.2, 0.3, 0.8, 0.9)
        """
        l, r, t, b = self._calculateActualMargin(left, right, top, bottom)
        self._setMargin(l, r, t, b)
        self._margins = [left, right, bottom, top]
        self._margins_act = [l, r, b, t]
        self.marginChanged.emit()

    def _calculateActualMargin(self, le, r, t, b):
        if le == 0:
            le = 0.2
        if r == 0:
            if self._canvas.axisIsValid("Right"):
                r = 0.80
            else:
                r = 0.85
        if b == 0:
            b = 0.2
        if t == 0:
            if self._canvas.axisIsValid("Top"):
                t = 0.80
            else:
                t = 0.85
        if le >= r:
            r = le + 0.05
        if b >= t:
            t = b + 0.05
        return le, r, t, b

    def getMargin(self, raw=False):
        """Set margin of canvas.

        Return:
            margin (float of length 4): The value of margin. If raw is False, actual margin used for display is returned. 
        """
        if raw:
            return self._margins
        else:
            return self._margins_act

    def _save(self, dictionary):
        dictionary['Margin'] = self._margins

    def _load(self, dictionary):
        if 'Margin' in dictionary:
            m = dictionary['Margin']
            self.setMargin(*m)

    def _setMargin(self):
        raise NotImplementedError()
