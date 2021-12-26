import warnings
from lys.errors import NotImplementedWarning
from .Font import FontInfo
from .SaveCanvas import CanvasPart, saveCanvas


class CanvasAxisLabel(CanvasPart):
    """
    Interface to access axis label of canvas. 
    All methods in this interface can be accessed from :class:`CanvasBase` instance.
    """

    def __init__(self, canvas):
        super().__init__(canvas)
        canvas.saveCanvas.connect(self._save)
        canvas.loadCanvas.connect(self._load)
        self.canvas().axisChanged.connect(self._axisChanged)
        self.__initialize()

    def __initialize(self):
        self._labels = {'Left': '', 'Right': '', 'Top': '', 'Bottom': ''}
        self._visible = {'Left': True, 'Right': True, 'Top': True, 'Bottom': True}
        self._coords = {'Left': -0.2, 'Right': -0.2, 'Top': -0.2, 'Bottom': -0.2}
        self._font = {}
        self.setAxisLabelVisible("Left", True)
        self.setAxisLabelVisible("Bottom", True)
        self.setAxisLabelCoords("Left", -0.2)
        self.setAxisLabelCoords("Bottom", -0.2)
        self.setAxisLabelFont("Left", FontInfo.defaultFamily())
        self.setAxisLabelFont("Bottom", FontInfo.defaultFamily())

    def _axisChanged(self, axis):
        self.setAxisLabelVisible(axis, True)
        self.setAxisLabelCoords(axis, -0.2)
        self.setAxisLabelFont(axis, FontInfo.defaultFamily())

    @saveCanvas
    def setAxisLabel(self, axis, text):
        if not self.canvas().axisIsValid(axis):
            return
        self._setAxisLabel(axis, text)
        self._labels[axis] = text

    def getAxisLabel(self, axis):
        if not self.canvas().axisIsValid(axis):
            return
        return self._labels[axis]

    @saveCanvas
    def setAxisLabelVisible(self, axis, b):
        if not self.canvas().axisIsValid(axis):
            return
        self._setAxisLabelVisible(axis, b)
        self._visible[axis] = b

    def getAxisLabelVisible(self, axis):
        if not self.canvas().axisIsValid(axis):
            return
        return self._visible[axis]

    @saveCanvas
    def setAxisLabelCoords(self, axis, pos):
        if not self.canvas().axisIsValid(axis):
            return
        self._setAxisLabelCoords(axis, pos)
        self._coords[axis] = pos

    def getAxisLabelCoords(self, axis):
        if not self.canvas().axisIsValid(axis):
            return
        return self._coords[axis]

    @saveCanvas
    def setAxisLabelFont(self, axis, family, size=10, color="black"):
        if not self.canvas().axisIsValid(axis):
            return
        if family not in FontInfo.fonts():
            warnings.warn("Font [" + family + "] not found. Use default font.")
            family = FontInfo.defaultFamily()
        self._setAxisLabelFont(axis, family, size, color)
        self._font[axis] = {"family": family, "size": size, "color": color}

    def getAxisLabelFont(self, axis):
        if not self.canvas().axisIsValid(axis):
            return
        return self._font[axis]

    def _save(self, dictionary):
        dic = {}
        for axis in self.canvas().axisList():
            dic[axis + "_label_on"] = self.getAxisLabelVisible(axis)
            dic[axis + "_label"] = self.getAxisLabel(axis)
            dic[axis + "_font"] = self.getAxisLabelFont(axis)
            dic[axis + "_pos"] = self.getAxisLabelCoords(axis)
        dictionary['LabelSetting'] = dic

    def _load(self, dictionary):
        if 'LabelSetting' in dictionary:
            dic = dictionary['LabelSetting']
            for axis in self.canvas().axisList():
                self.setAxisLabelVisible(axis, dic[axis + "_label_on"])
                self.setAxisLabel(axis, dic[axis + '_label'])
                self.setAxisLabelFont(axis, **dic[axis + "_font"])
                self.setAxisLabelCoords(axis, dic[axis + "_pos"])

    def _setAxisLabel(self, axis, text):
        warnings.warn(str(type(self)) + " does not implement _setAxisLabel(axis, text) method.", NotImplementedWarning)

    def _setAxisLabelVisible(self, axis, b):
        warnings.warn(str(type(self)) + " does not implement _setAxisLabelVisible(axis, b) method.", NotImplementedWarning)

    def _setAxisLabelCoords(self, axis, pos):
        warnings.warn(str(type(self)) + " does not implement _setAxisLabelCoords(axis, pos) method.", NotImplementedWarning)

    def _setAxisLabelFont(self, axis, name, size, color):
        warnings.warn(str(type(self)) + " does not implement _setAxisLabelFont(axis, name, size, color) method.", NotImplementedWarning)


class CanvasTickLabel(CanvasPart):
    """
    Interface to access tick label of canvas. 
    All methods in this interface can be accessed from :class:`CanvasBase` instance.
    """

    def __init__(self, canvas):
        super().__init__(canvas)
        # canvas.saveCanvas.connect(self._save)
        # canvas.loadCanvas.connect(self._load)
        # self.canvas().axisChanged.connect(self._axisChanged)
        # self.__initialize()
