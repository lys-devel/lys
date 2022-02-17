import warnings
from lys.errors import NotImplementedWarning
from .Font import FontInfo
from .CanvasBase import CanvasPart, saveCanvas


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
        """
        Set the label of *axis*.

        Args:
            axis('Left' or 'Right' or 'Top' or 'Bottom'): The axis.
            text(str): Label to be set.
        """
        if not self.canvas().axisIsValid(axis):
            return
        self._setAxisLabel(axis, text)
        self._labels[axis] = text

    def getAxisLabel(self, axis):
        """
        Get the label of *axis*

        Args:
            axis('Left' or 'Right' or 'Top' or 'Bottom'): The axis.

        Return:
            str: The text of the label.
        """
        if not self.canvas().axisIsValid(axis):
            return
        return self._labels[axis]

    @saveCanvas
    def setAxisLabelVisible(self, axis, show):
        """
        Show/hide the label.

        Args:
            axis('Left' or 'Right' or 'Top' or 'Bottom'): The axis.
            show(bool): The label is shown when *show* is True.
        """
        if not self.canvas().axisIsValid(axis):
            return
        self._setAxisLabelVisible(axis, show)
        self._visible[axis] = show

    def getAxisLabelVisible(self, axis):
        """
        Get the visibility of the label.

        Args:
            axis('Left' or 'Right' or 'Top' or 'Bottom'): The axis.

        Return:
            bool: True if the label is shown.
        """
        if not self.canvas().axisIsValid(axis):
            return
        return self._visible[axis]

    @saveCanvas
    def setAxisLabelCoords(self, axis, pos):
        """
        Set the position of the label.

        Args:
            axis('Left' or 'Right' or 'Top' or 'Bottom'): The axis.
            pos(float): The position of the label. Usually negative around -0.2.
        """
        if not self.canvas().axisIsValid(axis):
            return
        self._setAxisLabelCoords(axis, pos)
        self._coords[axis] = pos

    def getAxisLabelCoords(self, axis):
        """
        Get the position of the label.

        Args:
            axis('Left' or 'Right' or 'Top' or 'Bottom'): The axis.

        Return:
            float: The position of the label. Usually negative around -0.2.
        """
        if not self.canvas().axisIsValid(axis):
            return
        return self._coords[axis]

    @saveCanvas
    def setAxisLabelFont(self, axis, family, size=10, color="black"):
        """
        Set the font of the label.

        Args:
            axis('Left' or 'Right' or 'Top' or 'Bottom'): The axis.
            family(str): The name of the font.
            size(int): The size of the font.
            color(str): The color of the font such as #111111.
        """
        if not self.canvas().axisIsValid(axis):
            return
        if family not in FontInfo.fonts():
            warnings.warn("Font [" + family + "] not found. Use default font.")
            family = FontInfo.defaultFamily()
        self._setAxisLabelFont(axis, family, size, color)
        self._font[axis] = {"family": family, "size": size, "color": color}

    def getAxisLabelFont(self, axis):
        """
        Get the font of the label.

        Args:
            axis('Left' or 'Right' or 'Top' or 'Bottom'): The axis.

        Return:
            dict: The information of font. See :meth:`setAxisLabelFont`
        """
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
        canvas.saveCanvas.connect(self._save)
        canvas.loadCanvas.connect(self._load)
        self.canvas().axisChanged.connect(self._axisChanged)
        self.__initialize()

    def __initialize(self):
        self._visible = {'Left': True, 'Right': True, 'Top': True, 'Bottom': True}
        self._visible_mirror = {'Left': False, 'Right': False, 'Top': False, 'Bottom': False}
        self._font = {}
        self.setTickLabelVisible("Left", True)
        self.setTickLabelVisible("Bottom", True)
        self.setTickLabelFont("Left", FontInfo.defaultFamily())
        self.setTickLabelFont("Bottom", FontInfo.defaultFamily())

    def _axisChanged(self, axis):
        if axis == "Right":
            self._setTickLabelVisible("Left", False, mirror=True)
            self._visible_mirror["Left"] = False
            self.setTickLabelVisible("Right", True)
            self.setTickLabelFont("Right", FontInfo.defaultFamily())
        if axis == "Top":
            self._setTickLabelVisible("Bottom", False, mirror=True)
            self._visible_mirror["Bottom"] = False
            self.setTickLabelVisible("Top", True)
            self.setTickLabelFont("Top", FontInfo.defaultFamily())

    @saveCanvas
    def setTickLabelVisible(self, axis, tf, mirror=False):
        """
        Show/hide the tick label.

        Args:
            axis('Left' or 'Right' or 'Top' or 'Bottom'): The axis.
            tf(bool): The label is shown when *show* is True.
            mirror(bool): show/hide mirror label when it is True.
        """

        if not self.canvas().axisIsValid(axis):
            return
        if axis == "Left":
            if mirror and tf:
                if self.canvas().axisIsValid("Right"):
                    warnings.warn("Could not show mirror label of left tick when right axis is valid.")
                    return
        if axis == "Bottom":
            if mirror and tf:
                if self.canvas().axisIsValid("Top"):
                    warnings.warn("Could not show mirror label of bottom tick when right axis is valid.")
                    return
        if axis == "Right":
            if mirror:
                warnings.warn("Could not show/hide mirror label of right tick.")
                return
        if axis == "Top":
            if mirror:
                warnings.warn("Could not show/hide mirror label of top tick.")
                return
        self._setTickLabelVisible(axis, tf, mirror)
        if mirror:
            self._visible_mirror[axis] = tf
        else:
            self._visible[axis] = tf

    def getTickLabelVisible(self, axis, mirror=False):
        """
        Get the visibility of the tick label.

        Args:
            axis('Left' or 'Right' or 'Top' or 'Bottom'): The axis.
            mirror(bool): return the visibility of mirror label when it is True.

        Return:
            bool: visibility of the tick label.
        """
        if not self.canvas().axisIsValid(axis):
            return
        if mirror:
            return self._visible_mirror[axis]
        else:
            return self._visible[axis]

    @saveCanvas
    def setTickLabelFont(self, axis, family, size=9, color="#000000"):
        """
        Set the font of the label.

        Args:
            axis('Left' or 'Right' or 'Top' or 'Bottom'): The axis.
            family(str): The name of the font.
            size(int): The size of the font.
            color(str): The color of the font such as #111111.
        """
        if not self.canvas().axisIsValid(axis):
            return
        self._setTickLabelFont(axis, family, size, color)
        self._font[axis] = {"family": family, "size": size, "color": color}

    def getTickLabelFont(self, axis):
        """
        Get the font of the label.

        Args:
            axis('Left' or 'Right' or 'Top' or 'Bottom'): The axis.

        Return:
            dict: The information of font. See :meth:`setTickLabelFont`
        """
        if not self.canvas().axisIsValid(axis):
            return
        return self._font[axis]

    def _save(self, dictionary):
        dic = {}
        for axis in self.canvas().axisList():
            dic[axis + "_label_on"] = self.getTickLabelVisible(axis)
            dic[axis + "_font"] = self.getTickLabelFont(axis)
        dictionary['TickLabelSetting'] = dic

    def _load(self, dictionary):
        if 'TickLabelSetting' in dictionary:
            dic = dictionary['TickLabelSetting']
            for axis in self.canvas().axisList():
                self.setTickLabelVisible(axis, dic[axis + "_label_on"])
                self.setTickLabelFont(axis, **dic[axis + "_font"])

    def _setTickLabelVisible(self, axis, tf, mirror=False):
        warnings.warn(str(type(self)) + " does not implement _setTickLabelVisible(axis, tf, mirror) method.", NotImplementedWarning)

    def _setTickLabelFont(self, axis, family, size, color):
        warnings.warn(str(type(self)) + " does not implement _setTickLabelFont(axis, family, size, color) method.", NotImplementedWarning)
