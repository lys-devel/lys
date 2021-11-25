from LysQt.QtCore import pyqtSignal
from .SaveCanvas import CanvasPart, saveCanvas


class MarginBase(CanvasPart):
    """
    Abstract base class for Margin. 
    All methods in this interface can be accessed from :class:`CanvasBase` instance.
    Developers should implement a abstract method _setMargin(left, right, bottom, top).

    Examples::

        from lys import display
        g = display([1,2,3])
        g.canvas.setMargin(0, 0.3, 0.8, 0.9) # 0 means auto
        print(g.canvas.getMargin())
        # (0.2, 0.3, 0.8, 0.9)
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
            if self.canvas().axisIsValid("Right"):
                r = 0.80
            else:
                r = 0.85
        if b == 0:
            b = 0.2
        if t == 0:
            if self.canvas().axisIsValid("Top"):
                t = 0.80
            else:
                t = 0.85
        if le >= r:
            r = le + 0.05
        if b >= t:
            t = b + 0.05
        return le, r, t, b

    def getMargin(self, raw=False):
        """Get margin of canvas.

        Return:
            float of length 4: The value of margin. If *raw* is False, actual margin used for display is returned. 
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


class CanvasSizeBase(CanvasPart):
    """
    Abstract base class of CanvasSize. 
    All methods in this interface can be accessed from :class:`CanvasBase` instance.
    Developers should implement abstract methods _setAuto, _setAbsolute, _setAspect, and _getSize.

    Examples::

        from lys import display
        g = display([1,2,3])
        g.canvas.setCanvasSize("Width", "Absolute", 4)
        g.canvas.setCanvasSize("Height", "Absolute", 5)
        print(g.canvas.getCanvasSize())
        # (4, 5)
    """

    canvasResized = pyqtSignal(object)
    """Emitted when canvas size is changed."""

    def __init__(self, canvas):
        super().__init__(canvas)
        self.__dic = {}
        self.__dic['Width'] = {'mode': 'Auto', 'value': 0, 'axis1': 'Left', 'axis2': 'Bottom'}
        self.__dic['Height'] = {'mode': 'Auto', 'value': 0, 'axis1': 'Left', 'axis2': 'Bottom'}

        canvas.marginChanged.connect(self._onAdjusted)
        canvas.axisRangeChanged.connect(self._onAdjusted)
        canvas.saveCanvas.connect(self._save)
        canvas.loadCanvas.connect(self._load)

    @saveCanvas
    def _onAdjusted(self):
        self.setCanvasSize('Width', **self.__dic['Width'])
        self.setCanvasSize('Height', **self.__dic['Height'])

    @saveCanvas
    def setCanvasSize(self, type, mode, value=0, axis1=None, axis2=None):
        """
        Set the size of the canvas.

        When *mode* is 'Auto', the canvas size is set to *value*, and is changed freely.
        If *value* is zero, it remains present canvas size.

        When *mode* is 'Absolute', the canvas size is set to *value* in cm.

        When *mode* is 'Per Unit', the canvas size is set to *value* \* (range of *axis1*).

        When *mode* is 'Aspect', the aspect ratio is set to *value*.

        When *mode* is 'Plan', the canvas size is set to *value* \* (range of *axis1*) / (range of *axis2*).

        Args:
            type ('Width' or 'Height'): specify which size is set.
            mode ('Auto' or 'Absolute' or 'Per Unit' or 'Aspect' or 'Plan'): see description.
            value (float): the value to be set.
            axis1 ('Left' or 'Right' or 'Bottom' or 'Top'): see description. 
            axis2 ('Left' or 'Right' or 'Bottom' or 'Top'): see description. 
        """
        other = {"Height": "Width", "Width": "Height"}
        if type == "Both":
            self.setCanvasSize("Width", mode, value, axis1, axis2)
            self.setCanvasSize("Height", mode, value, axis1, axis2)
            return
        if mode in ["Aspect", "Plan"] and self.__dic[other[type]]["mode"] in ["Aspect", "Plan"]:
            return
        self.__dic[type] = {"mode": mode, "value": value, "axis1": axis1, "axis2": axis2}
        if mode == "Auto":
            if value != 0:
                self._setAbsolute(type, value)
            self._setAuto(type)
        elif value == 0:
            return
        elif mode == 'Absolute':
            self._setAbsolute(type, value)
            if self.__dic[other[type]]["mode"] in ["Aspect", "Plan"]:
                self.setCanvasSize(other[type], **self.__dic[other[type]])
        elif mode == 'Per Unit':
            ran = self.canvas().getAxisRange(axis1)
            self._setAbsolute(type, value * abs(ran[1] - ran[0]))
            if self.__dic[other[type]]["mode"] in ["Aspect", "Plan"]:
                self.setCanvasSize(other[type], **self.__dic[other[type]])
        elif mode == 'Aspect':
            self._setAspect(type, value)
        elif mode == 'Plan':
            ran1 = self.canvas().getAxisRange(axis1)
            ran2 = self.canvas().getAxisRange(axis2)
            self._setAspect(type, value * abs(ran1[1] - ran1[0]) / abs(ran2[1] - ran2[0]))
        self.canvasResized.emit(self.canvas())

    def getCanvasSize(self):
        """Get canvas size.

         Return:
            float of length 2: Canvas size. 
         """
        return self._getSize()

    def getSizeParams(self, type):
        """
        Get size parameters (mode, value, axis1, axis2) as dictionary. 

        See :meth:`setCanvasSize` for the description of each parameters

        Return:
            dictionary: size parameters. 
        """
        return self.__dic[type]

    @ saveCanvas
    def parentResized(self):
        wp = self.__dic['Width']['mode']
        hp = self.__dic['Height']['mode']
        if wp in ['Aspect', 'Plan'] and hp == 'Auto':
            self.setCanvasSize('Width', **self.__dic['Width'])
        if hp in ['Aspect', 'Plan'] and wp == 'Auto':
            self.setCanvasSize('Height', **self.__dic['Height'])

    def _save(self, dictionary):
        dic = {}
        size = self.getCanvasSize()
        if self.__dic['Width']['mode'] == 'Auto':
            self.__dic['Width']['value'] = size[0]
        if self.__dic['Height']['mode'] == 'Auto':
            self.__dic['Height']['value'] = size[1]
        dic['Width'] = [self.__dic['Width']['mode'], self.__dic['Width']['value'], self.__dic['Width']['axis1'], self.__dic['Width']['axis2']]
        dic['Height'] = [self.__dic['Height']['mode'], self.__dic['Height']['value'], self.__dic['Height']['axis1'], self.__dic['Height']['axis2']]
        dictionary['Size'] = dic

    def _load(self, dictionary):
        if 'Size' in dictionary:
            dic = dictionary['Size']
            if dic['Width'][0] in ['Aspect', 'Plan']:
                self.setCanvasSize('Height', *dic['Height'])
                self.setCanvasSize('Width', *dic['Width'])
            else:
                self.setCanvasSize('Width', *dic['Width'])
                self.setCanvasSize('Height', *dic['Height'])

    def _setAuto(self, axis):
        raise NotImplementedError

    def _setAbsolute(self, type, value):
        raise NotImplementedError

    def _setAspect(self, type, aspect):
        raise NotImplementedError

    def _getSize(self):
        raise NotImplementedError
