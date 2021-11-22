import numpy as np
from LysQt.QtCore import pyqtSignal
from .SaveCanvas import CanvasPart, saveCanvas


class CanvasAxes(CanvasPart):
    axisRangeChanged = pyqtSignal()

    def __init__(self, canvas):
        super().__init__(canvas)
        canvas.axisChanged.connect(lambda ax: self.setAutoScaleAxis(ax))
        canvas.saveCanvas.connect(self._save)
        canvas.loadCanvas.connect(self._load)
        self.__initialize()

    def __initialize(self):
        self.__auto = {'Left': True, 'Right': True, 'Top': True, 'Bottom': True}
        self.__range = {'Left': None, 'Right': None, 'Top': None, 'Bottom': None}
        self.__thick = {'Left': 1, 'Right': 1, 'Top': 1, 'Bottom': 1}
        self.__color = {'Left': "#000000", 'Right': "#000000", 'Top': "#000000", 'Bottom': "#000000"}
        self.__mirror = {'Left': True, 'Right': True, 'Top': True, 'Bottom': True}
        self.__mode = {'Left': "linear", 'Right': "linear", 'Top': "linear", 'Bottom': "linear"}
        for ax in self.axisList():
            self.setAutoScaleAxis(ax)
            self.setAxisThick(ax, 1)
            self.setAxisColor(ax, "#000000")
            self.setMirrorAxis(ax, True)
            self.setAxisMode(ax, "linear")

    def axisIsValid(self, axis):
        return self._isValid(axis)

    def axisList(self):
        res = ['Left']
        if self.axisIsValid('Right'):
            res.append('Right')
        res.append('Bottom')
        if self.axisIsValid('Top'):
            res.append('Top')
        return res

    @saveCanvas
    def setAxisRange(self, axis, range):
        if self.axisIsValid(axis):
            self._setRange(axis, range)
            self.__auto[axis] = False
            self.__range[axis] = range
            self.axisRangeChanged.emit()

    def getAxisRange(self, axis):
        if self.axisIsValid(axis):
            return self.__range[axis]

    @saveCanvas
    def setAutoScaleAxis(self, axis):
        if not self.axisIsValid(axis):
            return
        r = self._calculateAutoRange(axis)
        self.setAxisRange(axis, r)
        self.__auto[axis] = True

    def _calculateAutoRange(self, axis):
        return [0, 1]
        max = np.nan
        min = np.nan
        with np.errstate(invalid='ignore'):
            if axis in ['Left', 'Right']:
                for l in self.canvas().getLines():
                    max = np.nanmax([*l.wave.data, max])
                    min = np.nanmin([*l.wave.data, min])
                for im in self.canvas().getImages():
                    max = np.nanmax([*im.wave.y, max])
                    min = np.nanmin([*im.wave.y, min])
            if axis in ['Top', 'Bottom']:
                for l in self.canvas().getLines():
                    max = np.nanmax([*l.wave.x, max])
                    min = np.nanmin([*l.wave.x, min])
                for im in self.canvas().getImages():
                    max = np.nanmax([*im.wave.x, max])
                    min = np.nanmin([*im.wave.x, min])
        if np.isnan(max) or np.isnan(min):
            return None
        if len(self.canvas().getImages()) == 0:
            mergin = (max - min) / 20
        else:
            mergin = 0
        r = self.getAxisRange(axis)
        if r[0] < r[1]:
            return [min - mergin, max + mergin]
        else:
            return [max + mergin, min - mergin]

    def isAutoScaled(self, axis):
        if self.axisIsValid(axis):
            return self.__auto[axis]

    @saveCanvas
    def setAxisThick(self, axis, thick):
        if self.axisIsValid(axis):
            self._setAxisThick(axis, thick)
            self.__thick[axis] = thick

    def getAxisThick(self, axis):
        if self.axisIsValid(axis):
            return self.__thick[axis]

    @saveCanvas
    def setAxisColor(self, axis, color):
        if self.axisIsValid(axis):
            self._setAxisColor(axis, color)
            self.__color[axis] = color

    def getAxisColor(self, axis):
        if self.axisIsValid(axis):
            return self.__color[axis]

    @saveCanvas
    def setMirrorAxis(self, axis, value):
        if self.axisIsValid(axis):
            self._setMirrorAxis(axis, value)
            self.__mirror[axis] = value

    def getMirrorAxis(self, axis):
        if self.axisIsValid(axis):
            return self.__mirror[axis]

    @saveCanvas
    def setAxisMode(self, axis, mode):
        if self.axisIsValid(axis):
            self._setAxisMode(axis, mode)
            self.__mode[axis] = mode

    def getAxisMode(self, axis):
        if self.axisIsValid(axis):
            return self.__mode[axis]

    def _save(self, dictionary):
        dic = {}
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
        raise NotImplementedError()

    def _setRange(self, axis, range):
        raise NotImplementedError()

    def _setAxisThick(self, axis, thick):
        raise NotImplementedError()

    def _setAxisColor(self, axis, color):
        raise NotImplementedError()

    def _setMirrorAxis(self, axis, value):
        raise NotImplementedError()

    def _setAxisMode(self, axis, mod):
        raise NotImplementedError()


class CanvasTicks(CanvasPart):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.__initialize()
        canvas.axisRangeChanged.connect(self._refreshTicks)
        canvas.dataChanged.connect(self._refreshTicks)
        canvas.saveCanvas.connect(self._save)
        canvas.loadCanvas.connect(self._load)

    def _refreshTicks(self):
        for ax in ['Left', 'Right', 'Top', 'Bottom']:
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

    @saveCanvas
    def setTickWidth(self, axis, value, which='major'):
        if not self.canvas().axisIsValid(axis):
            return
        if which == 'both':
            self.setTickWidth(axis, value, 'major')
            self.setTickWidth(axis, value, 'minor')
            return
        self._setTickWidth(axis, value, which)
        self.__width[which][axis] = value

    def getTickWidth(self, axis, which='major'):
        if not self.canvas().axisIsValid(axis):
            return
        return self.__width[which][axis]

    @saveCanvas
    def setTickLength(self, axis, value, which='major'):
        if not self.canvas().axisIsValid(axis):
            return
        if which == 'both':
            self.setTickLength(axis, value, 'major')
            self.setTickLength(axis, value, 'minor')
            return
        self._setTickLength(axis, value, which)
        self.__length[which][axis] = value

    def getTickLength(self, axis, which='major'):
        if not self.canvas().axisIsValid(axis):
            return
        return self.__length[which][axis]

    @saveCanvas
    def setTickInterval(self, axis, value=0, which='major'):
        if not self.canvas().axisIsValid(axis):
            return
        if which == 'both':
            self.setTickInterval(axis, value, 'major')
            self.setTickInterval(axis, value, 'minor')
            return
        self._setTickInterval(axis, self._getInterval(axis, value, which), which)
        self.__interval[which][axis] = value

    def getTickInterval(self, axis, which='major', raw=True):
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
        p = 10**(np.floor(np.log10(d)))
        if d / p < 2:
            d = 1
        if d / p < 3:
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

    @saveCanvas
    def setTickVisible(self, axis, value, mirror=False, which='both'):
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
        if not self.canvas().axisIsValid(axis):
            return
        if mirror:
            return self.__visible[which + "_mirror"][axis]
        else:
            return self.__visible[which][axis]

    @saveCanvas
    def setTickDirection(self, axis, direction):
        if not self.canvas().axisIsValid(axis):
            return
        if direction == 1:
            direction = "in"
        if direction == -1:
            direction = "out"
        self._setTickDirection(axis, direction)
        self.__direction[axis] = direction

    def getTickDirection(self, axis):
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
                    self.setTickVisible(ax, dic[ax + "_major_on"], mirror=False, which='major')
                    self.setTickVisible(ax, dic[ax + "_majorm_on"], mirror=True, which='major')
                    self.setTickLength(ax, dic[ax + "_ticklen"])
                    self.setTickWidth(ax, dic[ax + "_tickwid"])
                    self.setTickInterval(ax, dic[ax + "_ticknum"])
                    self.setTickVisible(ax, dic[ax + "_minor_on"], mirror=False, which='minor')
                    self.setTickVisible(ax, dic[ax + "_minorm_on"], mirror=True, which='minor')
                    self.setTickLength(ax, dic[ax + "_ticklen2"], which='minor')
                    self.setTickWidth(ax, dic[ax + "_tickwid2"], which='minor')
                    self.setTickInterval(ax, dic[ax + "_ticknum2"], which='minor')
                    self.setTickDirection(ax, dic[ax + "_tickdir"])

    def _setTickWidth(self, axis, value, which):
        raise NotImplementedError()

    def _setTickLength(self, axis, value, which):
        raise NotImplementedError()

    def _setTickInterval(self, axis, interval, which='major'):
        raise NotImplementedError()

    def _setTickVisible(self, axis, tf, mirror, which='both'):
        raise NotImplementedError()

    def _setTickDirection(self, axis, direction):
        raise NotImplementedError()
