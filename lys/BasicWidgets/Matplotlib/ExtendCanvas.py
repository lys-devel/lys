
from PyQt5.QtGui import *

from lys.widgets import LysSubWindow

from .CanvasBase import *


class ExtendCanvas(FigureCanvasBase):
    savedDict = {}

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

    def SaveSetting(self, type):
        dict = {}
        self.SaveAsDictionary(dict)
        ExtendCanvas.savedDict[type] = dict[type]
        return dict[type]

    def LoadSetting(self, type, obj=None):
        if obj is not None:
            d = {}
            d[type] = obj
            self.LoadFromDictionary(d)
        elif type in ExtendCanvas.savedDict:
            d = {}
            d[type] = ExtendCanvas.savedDict[type]
            self.LoadFromDictionary(d)
