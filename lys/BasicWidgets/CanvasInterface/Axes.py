import warnings
import numpy as np
from LysQt.QtCore import pyqtSignal
from lys.errors import NotImplementedWarning
from .CanvasBase import CanvasPart, saveCanvas


class CanvasAxes(CanvasPart):
    """
    Interface to access axes of canvas.
    All methods in this interface can be accessed from :class:`CanvasBase` instance.
    Developers should implement a abstract methods.
    """
    axisChanged = pyqtSignal(str)
    """Emitted when the right or top axis is added."""

    axisRangeChanged = pyqtSignal()
    """Emitted when the range of axes is changed."""

    def __init__(self, canvas):
        super().__init__(canvas)
        self.axisChanged.connect(lambda ax: self.setAutoScaleAxis(ax))
        canvas.dataChanged.connect(self._update)
        canvas.saveCanvas.connect(self._save)
        canvas.loadCanvas.connect(self._load)
        canvas.initCanvas.connect(self._init)
        self.__initialize()

    def __initialize(self):
        self.__axisList = ["Left", "Bottom"]
        self.__auto = {'Left': True, 'Right': True, 'Top': True, 'Bottom': True}
        self.__range = {'Left': [0, 1], 'Right': [0, 1], 'Top': [0, 1], 'Bottom': [0, 1]}
        self.__thick = {'Left': 1, 'Right': 1, 'Top': 1, 'Bottom': 1}
        self.__color = {'Left': "#000000", 'Right': "#000000", 'Top': "#000000", 'Bottom': "#000000"}
        self.__mirror = {'Left': True, 'Right': True, 'Top': True, 'Bottom': True}
        self.__mode = {'Left': "linear", 'Right': "linear", 'Top': "linear", 'Bottom': "linear"}

    def _init(self):
        for ax in self.axisList():
            self.setAutoScaleAxis(ax)
            self.setAxisThick(ax, 1)
            self.setAxisColor(ax, "#000000")
            self.setMirrorAxis(ax, True)
            self.setAxisMode(ax, "linear")

    def _update(self):
        for ax in self.canvas().axisList():
            if self.isAutoScaled(ax):
                self.setAutoScaleAxis(ax)

    @ saveCanvas
    def addAxis(self, axis):
        """
        Add top/right axis to the canvas.

        Args:
            axis('Top' or 'Right'): The axis to be added.
        """
        if not self.axisIsValid(axis):
            self.__axisList.append(axis)
            self._addAxis(axis)
            self.axisChanged.emit(axis)

    def axisIsValid(self, axis):
        """
        Return if the specified *axis* is valid.

        Args:

            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The name of axis.

        Return:

            bool: The axis is valid or not.

        Example::

            from lys import display
            g = display([1,2,3])
            g.canvas.axisIsValid("Left")
            # True
            g.canvas.axisIsValid("Right")
            # False
        """
        return axis in self.__axisList

    def axisList(self):
        """
        Return list of valid axes.

        Return:

            list of axis name: The list of valid axes.

        Example::

            from lys import display
            g = display([1,2,3])
            g.canvas.axisList()
            # ['Left', 'Bottom']
        """
        return self.__axisList

    @ saveCanvas
    def setAxisRange(self, axis, range):
        """
        Set the axis view limits.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose range is changed.
            range (length 2 sequence): minimum and maximum range of view.

        Example::

            from lys import display
            g = display([1,2,3])
            g.canvas.setAxisRange('Left', [0, 5])
            g.canvas.getAxisRange('Left')
            # [0, 5]

        See also:
            :meth:`getAxisRange`, :meth:`setAutoScaleAxis`
        """
        if self.axisIsValid(axis):
            self._setRange(axis, range)
            self.__auto[axis] = False
            self.__range[axis] = range
            self.axisRangeChanged.emit()

    def getAxisRange(self, axis):
        """
        Get the axis view limits.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose range is changed.

        See also:
            :meth:`setAxisRange`, :meth:`setAutoScaleAxis`
        """
        if self.axisIsValid(axis):
            return self.__range[axis]

    @ saveCanvas
    def setAutoScaleAxis(self, axis):
        """
        Autoscale the axis view to the data.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose range is changed.

        Example::

            from lys import display
            g = display([1,2,3])
            g.canvas.setAutoScaleAxis('Left')
            g.canvas.getAxisRange('Left')
            # [-0.1, 2,1]

        See also:
            :meth:`setAxisRange`, :meth:`getAxisRange`, :meth:`isAutoScaled`
        """
        if not self.axisIsValid(axis):
            return
        r = self._calculateAutoRange(axis)
        self.setAxisRange(axis, r)
        self.__auto[axis] = True

    def _calculateAutoRange(self, axis):
        max = np.nan
        min = np.nan
        data = [wdata for wdata in self.canvas().getWaveData() if axis in wdata.getAxis()]
        if len(data) == 0:
            return [0, 1]
        index = {"Left": 1, "Right": 1, "Bottom": 0, "Top": 0}[axis]
        for d in data:
            wav = d.getFilteredWave()
            if wav.data.ndim == 1 and index == 1:
                ax = wav.data
            else:
                ax = wav.getAxis(index)
            max = np.nanmax([*ax, max])
            min = np.nanmin([*ax, min])
        if len(self.canvas().getLines()) == len(data):
            mergin = (max - min) / 20
        else:
            mergin = 0
        r = self.getAxisRange(axis)
        if r[0] < r[1]:
            return [min - mergin, max + mergin]
        else:
            return [max + mergin, min - mergin]

    def isAutoScaled(self, axis):
        """
        Return if the specified *axis* is auto-scaled.

        Args:

            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The name of axis.

        Return:

            bool: The axis is auto-scaled or not.

        Example::

            from lys import display
            g = display([1,2,3])
            g.canvas.setRange('Bottom', [0, 3])
            g.canvas.isAutoScaled('Left')
            # True
            g.canvas.isAutoScaled('Bottom')
            # False

        See also:
            :meth:`setAxisRange`, :meth:`getAxisRange`, :meth:`setAutoScaleAxis`

        """
        if self.axisIsValid(axis):
            return self.__auto[axis]

    @ saveCanvas
    def setAxisThick(self, axis, thick):
        """
        Set thick of axis.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose thick is changed.
            thick (float): The thickness of the axis.

        See also:
            :meth:`getAxisThick`
        """
        if self.axisIsValid(axis):
            self._setAxisThick(axis, thick)
            self.__thick[axis] = thick

    def getAxisThick(self, axis):
        """
        Get thick of axis.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose thick is obtained.

        Return:
            float: The thickness of the axis.

        See also:
            :meth:`setAxisThick`
        """
        if self.axisIsValid(axis):
            return self.__thick[axis]

    @ saveCanvas
    def setAxisColor(self, axis, color):
        """
        Set color of axis.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose thick is changed.
            color (str): The color code of the axis, such as '#123456'.

        See also:
            :meth:`getAxisColor`
        """
        if self.axisIsValid(axis):
            self._setAxisColor(axis, color)
            self.__color[axis] = color

    def getAxisColor(self, axis):
        """
        Get color of axis.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose thick is changed.

        Return:
            str: The color code of the axis, such as '#123456'.

        See also:
            :meth:`setAxisColor`
        """
        if self.axisIsValid(axis):
            return self.__color[axis]

    @ saveCanvas
    def setMirrorAxis(self, axis, value):
        """
        Enable/disable mirror axis.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose mirror axis is enabled/disabled.
            value (bool): If *value* is True (False), the mirror axis is shown (hidden).

        See also:
            :meth:`getMirrorAxis`
        """
        if self.axisIsValid(axis):
            self._setMirrorAxis(axis, value)
            self.__mirror[axis] = value

    def getMirrorAxis(self, axis):
        """
        Get the state of mirror axis.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose mirror axis state is checked.

        Return:
            bool: If *value* is True (False), the mirror axis is shown (hidden).

        See also:
            :meth:`setMirrorAxis`
        """
        if self.axisIsValid(axis):
            return self.__mirror[axis]

    @ saveCanvas
    def setAxisMode(self, axis, mode):
        """
        Set axis mode.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose mirror axis is enabled/disabled.
            mode ('linear' or 'log'): The scale of the axis is set to *mode*.

        See also:
            :meth:`setAxisMode`
        """
        if self.axisIsValid(axis):
            self._setAxisMode(axis, mode)
            self.__mode[axis] = mode

    def getAxisMode(self, axis):
        """
        Get axis mode.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose mode is changed.

        Return:
            'linear' or 'log': The scale mode of the axis.

        See also:
            :meth:`getAxisMode`
        """
        if self.axisIsValid(axis):
            return self.__mode[axis]

    def _save(self, dictionary):
        dic = {}
        dictionary['AxisList'] = self.axisList()
        list = ['Left', 'Right', 'Top', 'Bottom']
        for ax in list:
            if self.axisIsValid(ax):
                dic[ax + "_auto"] = self.isAutoScaled(ax)
                dic[ax] = self.getAxisRange(ax)
            else:
                dic[ax + "_auto"] = None
                dic[ax] = None
        dictionary['AxisRange'] = dic

        dic = {}
        for ax in ['Left', 'Right', 'Top', 'Bottom']:
            if self.axisIsValid(ax):
                dic[ax + "_mode"] = self.getAxisMode(ax)
                dic[ax + "_mirror"] = self.getMirrorAxis(ax)
                dic[ax + "_color"] = self.getAxisColor(ax)
                dic[ax + "_thick"] = self.getAxisThick(ax)
            else:
                dic[ax + "_mode"] = None
                dic[ax + "_mirror"] = None
                dic[ax + "_color"] = None
                dic[ax + "_thick"] = None
        dictionary['AxisSetting'] = dic

    def _load(self, dictionary):
        if 'AxisList' in dictionary:
            for ax in dictionary['AxisList']:
                self.addAxis(ax)
        if 'AxisRange' in dictionary:
            dic = dictionary['AxisRange']
            for ax in ['Left', 'Right', 'Top', 'Bottom']:
                auto = dic[ax + "_auto"]
                if auto is not None:
                    if auto:
                        self.setAutoScaleAxis(ax)
                    else:
                        self.setAxisRange(ax, dic[ax])

        if 'AxisSetting' in dictionary:
            dic = dictionary['AxisSetting']
            for ax in ['Left', 'Right', 'Top', 'Bottom']:
                if self.axisIsValid(ax):
                    self.setAxisMode(ax, dic[ax + "_mode"])
                    self.setMirrorAxis(ax, dic[ax + "_mirror"])
                    self.setAxisColor(ax, dic[ax + "_color"])
                    self.setAxisThick(ax, dic[ax + "_thick"])

    def _isValid(self, axis):
        raise NotImplementedError(str(type(self)) + " does not implement _isValid(axis) method.")

    def _setRange(self, axis, range):
        raise NotImplementedError(str(type(self)) + " does not implement _setRange(axis, range) method.")

    def _setAxisThick(self, axis, thick):
        warnings.warn(str(type(self)) + " does not implement _setRange(axis, range) method.", NotImplementedWarning)

    def _setAxisColor(self, axis, color):
        warnings.warn(str(type(self)) + " does not implement _setAxisColor(axis, color) method.", NotImplementedWarning)

    def _setMirrorAxis(self, axis, value):
        warnings.warn(str(type(self)) + " does not implement _setMirrorAxis(axis, value) method.", NotImplementedWarning)

    def _setAxisMode(self, axis, mod):
        warnings.warn(str(type(self)) + " does not implement _setAxisMode(axis, mode) method.", NotImplementedWarning)


class CanvasTicks(CanvasPart):
    """
    Interface to access ticks of canvas.
    All methods in this interface can be accessed from :class:`CanvasBase` instance.
    Developers should implement a abstract methods.
    """

    def __init__(self, canvas):
        super().__init__(canvas)
        self.__initialize()
        canvas.axisRangeChanged.connect(self._refreshTicks)
        canvas.dataChanged.connect(self._refreshTicks)
        canvas.saveCanvas.connect(self._save)
        canvas.loadCanvas.connect(self._load)

    def _refreshTicks(self):
        for ax in self.canvas().axisList():
            for t in ['major', 'minor']:
                self.setTickInterval(ax, self.getTickInterval(ax, t), t)

    def __initialize(self):
        self.__width = {}
        self.__width['major'] = {'Left': 1, 'Right': 1, 'Top': 1, 'Bottom': 1}
        self.__width['minor'] = {'Left': 1, 'Right': 1, 'Top': 1, 'Bottom': 1}

        self.__length = {}
        self.__length['major'] = {'Left': 3.5, 'Right': 3.5, 'Top': 3.5, 'Bottom': 3.5}
        self.__length['minor'] = {'Left': 2, 'Right': 2, 'Top': 2, 'Bottom': 2}

        self.__interval = {}
        self.__interval['major'] = {'Left': 0, 'Right': 0, 'Top': 0, 'Bottom': 0}
        self.__interval['minor'] = {'Left': 0, 'Right': 0, 'Top': 0, 'Bottom': 0}

        self.__visible = {}
        self.__visible['major'] = {'Left': True, 'Right': True, 'Top': True, 'Bottom': True}
        self.__visible['major_mirror'] = {'Left': True, 'Right': True, 'Top': True, 'Bottom': True}
        self.__visible['minor'] = {'Left': False, 'Right': False, 'Top': False, 'Bottom': False}
        self.__visible['minor_mirror'] = {'Left': False, 'Right': False, 'Top': False, 'Bottom': False}

        self.__direction = {'Left': 'in', 'Right': 'in', 'Top': 'in', 'Bottom': 'in'}

        for ax in self.canvas().axisList():
            self.setTickWidth(ax, 1, which='both')
            self.setTickLength(ax, 2, which='minor')
            self.setTickLength(ax, 3.5, which='major')
            self.setTickInterval(ax, 0, which='both')
            self.setTickVisible(ax, True, mirror=False, which='major')
            self.setTickVisible(ax, False, mirror=False, which='minor')
            self.setTickVisible(ax, False, mirror=True, which='both')
            self.setTickDirection(ax, "in")

    @ saveCanvas
    def setTickWidth(self, axis, value, which='major'):
        """
        Set thick of ticks.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose ticks are changed.
            value (float): The width of the axis.
            which ('major' or 'minor' or 'both'): Change major (minor) tick width depending on *which*.

        See also:
            :meth:`getTickWidth`
        """
        if not self.canvas().axisIsValid(axis):
            return
        if which == 'both':
            self.setTickWidth(axis, value, 'major')
            self.setTickWidth(axis, value, 'minor')
            return
        self._setTickWidth(axis, value, which)
        self.__width[which][axis] = value

    def getTickWidth(self, axis, which='major'):
        """
        Get thick of ticks.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose ticks are changed.
            which ('major' or 'minor'): Return major (minor) tick width depending on *which*.

        Return:
            float: The width of the ticks.

        See also:
            :meth:`setTickWidth`
        """
        if not self.canvas().axisIsValid(axis):
            return
        return self.__width[which][axis]

    @ saveCanvas
    def setTickLength(self, axis, value, which='major'):
        """
        Set length of ticks.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose ticks are changed.
            value (float): The length of the axis.
            which ('major' or 'minor' or 'both'): Change major (minor) tick length depending on *which*.

        See also:
            :meth:`getTickLength`
        """
        if not self.canvas().axisIsValid(axis):
            return
        if which == 'both':
            self.setTickLength(axis, value, 'major')
            self.setTickLength(axis, value, 'minor')
            return
        self._setTickLength(axis, value, which)
        self.__length[which][axis] = value

    def getTickLength(self, axis, which='major'):
        """
        Get length of ticks.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose ticks are changed.
            which ('major' or 'minor' or 'both'): Return major (minor) tick length depending on *which*.

        Return:
            float: The length of the ticks.

        See also:
            :meth:`setTickLength`
        """
        if not self.canvas().axisIsValid(axis):
            return
        return self.__length[which][axis]

    @ saveCanvas
    def setTickInterval(self, axis, value=0, which='major'):
        """
        Set interval of ticks.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose ticks are changed.
            value (float): The length of the axis. Zero means automatic interval.
            which ('major' or 'minor' or 'both'): Change major (minor) tick length depending on *which*.

        See also:
            :meth:`getTickInterval`
        """
        if not self.canvas().axisIsValid(axis):
            return
        if which == 'both':
            self.setTickInterval(axis, value, 'major')
            self.setTickInterval(axis, value, 'minor')
            return
        self._setTickInterval(axis, self._getInterval(axis, value, which), which)
        self.__interval[which][axis] = value

    def getTickInterval(self, axis, which='major', raw=True):
        """
        Get interval of ticks.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose ticks are changed.
            which ('major' or 'minor'): Return major (minor) tick interval depending on *which*.

        Return:
            float: The interval of the ticks.

        See also:
            :meth:`setTickInterval`
        """
        if not self.canvas().axisIsValid(axis):
            return
        if raw:
            return self.__interval[which][axis]
        else:
            return self._getInterval(axis, self.__interval[which][axis], which)

    def _getInterval(self, axis, value, which):
        if value == 0:
            return self._calculateAutoInterval(axis, which)
        else:
            range = self.canvas().getAxisRange(axis)
            if (abs(range[1] - range[0]) / value) < 100:
                return value
            else:
                return self._calculateAutoInterval(axis, which)

    def _calculateAutoInterval(self, axis, which):
        range = self.canvas().getAxisRange(axis)
        d = abs(range[1] - range[0]) / 4
        if d == 0:
            return 1
        p = 10**(np.floor(np.log10(d)))
        if d / p < 2:
            d = 1
        elif d / p < 3:
            d = 2
        elif d / p < 8:
            d = 5
        else:
            d = 10
        if which == 'major':
            return d * p
        else:
            if d == 2:
                return d * p / 4
            return d * p / 5

    @ saveCanvas
    def setTickVisible(self, axis, value, mirror=False, which='both'):
        """
        Set visibility of ticks.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose ticks are changed.
            value (bool): If it is True (False), the ticks are shown (hidden).
            which ('major' or 'minor' or 'both'): Change major (minor) tick length depending on *which*.

        See also:
            :meth:`getTickVisible`
        """
        if not self.canvas().axisIsValid(axis):
            return
        if which == 'both':
            self.setTickVisible(axis, value, mirror, 'major')
            self.setTickVisible(axis, value, mirror, 'minor')
            return
        self._setTickVisible(axis, value, mirror, which)
        if mirror:
            self.__visible[which + "_mirror"][axis] = value
        else:
            self.__visible[which][axis] = value

    def getTickVisible(self, axis, mirror=False, which='major'):
        """
        Get visibility of ticks.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose ticks are changed.
            which ('major' or 'minor'): This method returns major (minor) tick visibility depending on *which*.

        See also:
            :meth:`setTickVisible`
        """
        if not self.canvas().axisIsValid(axis):
            return
        if mirror:
            return self.__visible[which + "_mirror"][axis]
        else:
            return self.__visible[which][axis]

    @ saveCanvas
    def setTickDirection(self, axis, direction):
        """
        Set direction of ticks.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose ticks are changed.
            value ('in' or 'out'): Whether the ticks are shown in the box.

        See also:
            :meth:`getTickDirection`
        """
        if not self.canvas().axisIsValid(axis):
            return
        if direction == 1:
            direction = "in"
        if direction == -1:
            direction = "out"
        self._setTickDirection(axis, direction)
        self.__direction[axis] = direction

    def getTickDirection(self, axis):
        """
        Get direction of ticks.

        Args:
            axis ('Left' or 'Right' or 'Bottom' or 'Top'): The axis whose ticks are changed.

        Return:
            'in' or 'out': This method returns whether the ticks are shown in the box.

        See also:
            :meth:`setTickDirection`
        """
        if not self.canvas().axisIsValid(axis):
            return
        return self.__direction[axis]

    def _save(self, dictionary):
        dic = {}
        for ax in ['Left', 'Right', 'Top', 'Bottom']:
            if self.canvas().axisIsValid(ax):
                dic[ax + "_major_on"] = self.getTickVisible(ax, mirror=False, which='major')
                dic[ax + "_majorm_on"] = self.getTickVisible(ax, mirror=True, which='major')
                dic[ax + "_ticklen"] = self.getTickLength(ax)
                dic[ax + "_tickwid"] = self.getTickWidth(ax)
                dic[ax + "_ticknum"] = self.getTickInterval(ax)
                dic[ax + "_minor_on"] = self.getTickVisible(ax, mirror=False, which='minor')
                dic[ax + "_minorm_on"] = self.getTickVisible(ax, mirror=True, which='minor')
                dic[ax + "_ticklen2"] = self.getTickLength(ax, which='minor')
                dic[ax + "_tickwid2"] = self.getTickWidth(ax, which='minor')
                dic[ax + "_ticknum2"] = self.getTickInterval(ax, which='minor')
                dic[ax + "_tickdir"] = self.getTickDirection(ax)
        dictionary['TickSetting'] = dic

    def _load(self, dictionary):
        if 'TickSetting' in dictionary:
            dic = dictionary['TickSetting']
            for ax in ['Left', 'Right', 'Top', 'Bottom']:
                if self.canvas().axisIsValid(ax):
                    self.setTickLength(ax, dic[ax + "_ticklen"])
                    self.setTickWidth(ax, dic[ax + "_tickwid"])
                    self.setTickInterval(ax, dic[ax + "_ticknum"])
                    self.setTickLength(ax, dic[ax + "_ticklen2"], which='minor')
                    self.setTickWidth(ax, dic[ax + "_tickwid2"], which='minor')
                    self.setTickInterval(ax, dic[ax + "_ticknum2"], which='minor')
                    self.setTickDirection(ax, dic[ax + "_tickdir"])
                    self.setTickVisible(ax, dic[ax + "_major_on"], mirror=False, which='major')
                    self.setTickVisible(ax, dic[ax + "_majorm_on"], mirror=True, which='major')
                    self.setTickVisible(ax, dic[ax + "_minor_on"], mirror=False, which='minor')
                    self.setTickVisible(ax, dic[ax + "_minorm_on"], mirror=True, which='minor')

    def _setTickWidth(self, axis, value, which):
        warnings.warn(str(type(self)) + " does not implement _setTickWidth(axis, value, which) method.", NotImplementedWarning)

    def _setTickLength(self, axis, value, which):
        warnings.warn(str(type(self)) + " does not implement _setTickLength(axis, value, which) method.", NotImplementedWarning)

    def _setTickInterval(self, axis, interval, which='major'):
        warnings.warn(str(type(self)) + " does not implement _setTickInterval(axis, interval, which) method.", NotImplementedWarning)

    def _setTickVisible(self, axis, tf, mirror, which='both'):
        warnings.warn(str(type(self)) + " does not implement _setTickVisible(axis, tf, mirror, which) method.", NotImplementedWarning)

    def _setTickDirection(self, axis, direction):
        warnings.warn(str(type(self)) + " does not implement _setTIckDirection(axis, direction) method.", NotImplementedWarning)
