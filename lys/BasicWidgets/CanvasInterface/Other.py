from lys.widgets import LysSubWindow

from .CanvasBase import CanvasPart, saveCanvas


class CanvasUtilities(CanvasPart):
    """
    Extra canvas utilities.
    """

    def openModifyWindow(self):
        from lys import ModifyWindow, Graph
        parent = self._getParent()
        mod = ModifyWindow(self.canvas(), parent, showArea=isinstance(parent, Graph))
        return mod

    def _getParent(self):
        parent = self.canvas().parentWidget()
        while(parent is not None):
            if isinstance(parent, LysSubWindow):
                return parent
            parent = parent.parentWidget()
