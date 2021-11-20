import numpy as np
from LysQt.QtCore import pyqtSignal
from .SaveCanvas import CanvasPart, saveCanvas


class CanvasAxes(CanvasPart):
    axisRangeChanged = pyqtSignal()

    def __init__(self, canvas):
        super().__init__(canvas)
        canvas.saveCanvas.connect(self._save)
        canvas.loadCanvas.connect(self._load)
        self.__auto = {'Left': True, 'Right': True, 'Top': True, 'Bottom': True}

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
        if not self.axisIsValid(axis):
            return
        self._setRange(axis, range)
        self.__auto[axis] = False
        self.axisRangeChanged.emit()

    def getAxisRange(self, axis):
        if not self.axisIsValid(axis):
            return None
        else:
            return self._getRange(axis)

    @saveCanvas
    def setAutoScaleAxis(self, axis):
        if not self.axisIsValid(axis):
            return
        r = self._calculateAutoRange(axis)
        self.setAxisRange(axis, r)
        self.__auto[axis] = True

    def _calculateAutoRange(self, axis):
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
        else:
            return None

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
