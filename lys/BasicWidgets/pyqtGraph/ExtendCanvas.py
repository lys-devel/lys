from .CanvasBase import FigureCanvasBase


class ExtendCanvas(FigureCanvasBase):
    savedDict = {}

    def SaveSetting(self, type):
        dict = {}
        self.SaveAsDictionary(dict)
        ExtendCanvas.savedDict[type] = dict[type]
        return dict[type]

    def LoadSetting(self, type, obj=None):
        if dict is not None:
            d = {}
            d[type] = dict
            self.LoadFromDictionary(d)
        elif type in ExtendCanvas.savedDict:
            d = {}
            d[type] = ExtendCanvas.savedDict[type]
            self.LoadFromDictionary(d)
