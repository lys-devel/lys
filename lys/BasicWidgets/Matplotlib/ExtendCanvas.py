
from PyQt5.QtGui import *

from lys.widgets import LysSubWindow

from .CanvasBase import *


class ExtendCanvas(FigureCanvasBase):

    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.doubleClicked.connect(self.defModFunc)

    def defModFunc(self, canvas, tab='Axis'):
        from lys import ModifyWindow, Graph
        parent = self.parentWidget()
        while(parent is not None):
            if isinstance(parent, LysSubWindow):
                mod = ModifyWindow(self, parent, showArea=isinstance(parent, Graph))
                mod.selectTab(tab)
                break
            parent = parent.parentWidget()
