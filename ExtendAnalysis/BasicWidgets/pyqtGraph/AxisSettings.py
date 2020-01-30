#!/usr/bin/env python
import random
import weakref
import sys
import os
import numpy as np
from enum import Enum
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ExtendAnalysis import *
from .CanvasBase import saveCanvas
from .ImageSettings import *


class RangeSelectableCanvas(ImageSettingCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi)
        self.roi = pg.RectROI([0, 0], [0, 0], invertible=True)
        self.roi.hide()
        self.roi.addScaleHandle([1, 1], [0, 0])
        self.roi.addScaleHandle([0, 0], [1, 1])
        self.roi.addScaleHandle([1, 0.5], [0, 0.5])
        self.roi.addScaleHandle([0, 0.5], [1, 0.5])
        self.roi.addScaleHandle([0.5, 0], [0.5, 1])
        self.roi.addScaleHandle([0.5, 1], [0.5, 0])
        self.axes.addItem(self.roi)

    def _onClick(self, event):
        if event.button() == Qt.LeftButton:
            if self.roi.isVisible():
                self.roi.hide()
        return super()._onClick(event)

    def _onDrag(self, event, axis=0):
        if event.button() == Qt.LeftButton:
            if event.isStart():
                self._roi_start = self.axes.mapSceneToView(event.scenePos())
                self.roi.setPos(self._roi_start)
                self.roi.show()
                event.accept()
                return
            else:
                self._roi_end = self.axes.mapSceneToView(event.scenePos())
                self.roi.setSize(self._roi_end - self._roi_start)
                event.accept()
                return
        return super()._onDrag(event)

    def IsRangeSelected(self):
        return self.roi.isVisible()

    def ClearSelectedRange(self):
        self.roi.hide()

    def SelectedRange(self):
        if self.roi.isVisible():
            return (np.array([self._roi_start.x(), self._roi_start.y()]), np.array([self._roi_end.x(), self._roi_end.y()]))
        else:
            return None


class AxisSelectableCanvas(RangeSelectableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.axis_selected = 'Left'
        self.__listener = []

    def setSelectedAxis(self, axis):
        self.axis_selected = axis
        self._emitAxisSelected()

    def getSelectedAxis(self):
        return self.axis_selected

    def addAxisSelectedListener(self, listener):
        self.__listener.append(weakref.ref(listener))

    def _emitAxisSelected(self):
        for l in self.__listener:
            if l() is not None:
                l().OnAxisSelected(self.axis_selected)
            else:
                self.__listener.remove(l)

    def getAxes(self, axis='Left'):
        ax = axis
        if ax in ['Left', 'Bottom']:
            return self.axes
        if ax == 'Top':
            if self.axes_ty is not None:
                return self.axes_ty
            else:
                return self.axes_txy
        if ax == 'Right':
            if self.axes_tx is not None:
                return self.axes_tx
            else:
                return self.axes_txy

    def axisIsValid(self, axis):
        if axis in ['Left', 'Bottom']:
            return True
        if axis in ['Top']:
            return self.axes_ty is not None or self.axes_txy is not None
        if axis in ['Right']:
            return self.axes_tx is not None or self.axes_txy is not None

    def axisList(self):
        res = ['Left']
        if self.axisIsValid('Right'):
            res.append('Right')
        res.append('Bottom')
        if self.axisIsValid('Top'):
            res.append('Top')
        return res


class AxisRangeAdjustableCanvas(AxisSelectableCanvas):
    axisRangeChanged = pyqtSignal()

    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.__listener = []
        self.fig.vb.sigRangeChanged.connect(self.axisRangeChanged)

    def SaveAsDictionary(self, dictionary, path):
        super().SaveAsDictionary(dictionary, path)
        dic = {}
        list = ['Left', 'Right', 'Top', 'Bottom']
        for l in list:
            if self.axisIsValid(l):
                dic[l + "_auto"] = self.isAutoScaled(l)
                dic[l] = self.getAxisRange(l)
            else:
                dic[l + "_auto"] = None
                dic[l] = None
        dictionary['AxisRange'] = dic

    def LoadFromDictionary(self, dictionary, path):
        super().LoadFromDictionary(dictionary, path)
        if 'AxisRange' in dictionary:
            dic = dictionary['AxisRange']
            for l in ['Left', 'Right', 'Top', 'Bottom']:
                auto = dic[l + "_auto"]
                if auto is not None:
                    if auto:
                        self.setAutoScaleAxis(l)
                    else:
                        self.setAxisRange(dic[l], l)

    @saveCanvas
    def setAxisRange(self, range, axis):
        axes = self.getAxes(axis)
        if axes is None:
            return self.setAxisRange(range, Opposite[axis])
        if axis in ['Left', 'Right']:
            axes.setYRange(*range, padding=0)
            axes.disableAutoRange(axis='y')
        if axis in ['Top', 'Bottom']:
            axes.setXRange(*range, padding=0)
            axes.disableAutoRange(axis='x')
        self.axisRangeChanged.emit()

    def getAxisRange(self, axis):
        axes = self.getAxes(axis)
        if axes is None:
            return self.getAxisRange(Opposite[axis])
        r = axes.viewRange()
        if axis in ['Left', 'Right']:
            return r[1]
        if axis in ['Top', 'Bottom']:
            return r[0]

    @saveCanvas
    def setAutoScaleAxis(self, axis):
        axes = self.getAxes(axis=axis)
        if axes is None:
            return self.setAutoScaleAxis(Opposite[axis])
        if axis in ['Left', 'Right']:
            axes.enableAutoRange(axis='y')
        if axis in ['Top', 'Bottom']:
            axes.enableAutoRange(axis='x')
        self.axisRangeChanged.emit()

    def isAutoScaled(self, axis):
        axes = self.getAxes(axis=axis)
        if axes is None:
            return self.isAutoScaled(Opposite[axis])
        if axis in ['Left', 'Right']:
            return axes.autoRangeEnabled()[1] != False
        if axis in ['Top', 'Bottom']:
            return axes.autoRangeEnabled()[0] != False


class AxisRangeRightClickCanvas(AxisRangeAdjustableCanvas):
    @saveCanvas
    def __ExpandAndShrink(self, mode, axis):
        if not self.axisIsValid(axis):
            return
        ax = self.getAxes(axis)
        pos, pos2 = self.SelectedRange()
        width = pos2[0] - pos[0]
        height = pos2[1] - pos[1]
        xlim = self.getAxisRange("Bottom")
        ylim = self.getAxisRange("Left")

        if axis in ['Bottom', 'Top']:
            if mode in ['Expand', 'Horizontal Expand']:
                minVal = min(pos[0], pos[0] + width)
                maxVal = max(pos[0], pos[0] + width)
                self.setAxisRange([minVal, maxVal], axis)
            if mode in ['Shrink', 'Horizontal Shrink']:
                ratio = abs((xlim[1] - xlim[0]) / width)
                a = min(pos[0], pos[0] + width)
                b = max(pos[0], pos[0] + width)
                minVal = xlim[0] - ratio * (a - xlim[0])
                maxVal = xlim[1] + ratio * (xlim[1] - b)
                self.setAxisRange([minVal, maxVal], axis)
        else:
            if mode in ['Vertical Expand', 'Expand']:
                if ylim[1] < ylim[0]:
                    minVal = max(pos[1], pos[1] + height)
                    maxVal = min(pos[1], pos[1] + height)
                else:
                    minVal = min(pos[1], pos[1] + height)
                    maxVal = max(pos[1], pos[1] + height)
                self.setAxisRange([minVal, maxVal], axis)
            if mode in ['Shrink', 'Vertical Shrink']:
                ratio = abs((ylim[1] - ylim[0]) / height)
                if ylim[1] < ylim[0]:
                    a = max(pos[1], pos[1] + height)
                    b = min(pos[1], pos[1] + height)
                else:
                    a = min(pos[1], pos[1] + height)
                    b = max(pos[1], pos[1] + height)
                minVal = ylim[0] - ratio * (a - ylim[0])
                maxVal = ylim[1] + ratio * (ylim[1] - b)
                self.setAxisRange([minVal, maxVal], axis)

    def constructContextMenu(self):
        menu = super().constructContextMenu()
        menu.addAction(QAction('Auto scale axes', self, triggered=self.__auto))
        if self.IsRangeSelected():
            m = menu.addMenu('Expand and Shrink')
            m.addAction(QAction('Expand', self, triggered=self.__expand))
            m.addAction(QAction('Horizontal Expand', self, triggered=self.__expandh))
            m.addAction(QAction('Vertical Expand', self, triggered=self.__expandv))
            m.addAction(QAction('Shrink', self, triggered=self.__shrink))
            m.addAction(QAction('Horizontal Shrink', self, triggered=self.__shrinkh))
            m.addAction(QAction('Vertical Shrink', self, triggered=self.__shrinkv))
        return menu

    def __expand(self):
        self.__exec('Expand')

    def __expandh(self):
        self.__exec('Horizontal Expand')

    def __expandv(self):
        self.__exec('Vertical Expand')

    def __shrink(self):
        self.__exec('Shrink')

    def __shrinkh(self):
        self.__exec('Horizontal Shrink')

    def __shrinkv(self):
        self.__exec('Vertical Shrink')

    def __exec(self, text):
        for axis in ['Left', 'Right', 'Top', 'Bottom']:
            self.__ExpandAndShrink(text, axis)
        self.ClearSelectedRange()

    def __auto(self):
        for axis in ['Left', 'Right', 'Bottom', 'Top']:
            self.setAutoScaleAxis(axis)
        self.ClearSelectedRange()


opposite = {'Left': 'right', 'Right': 'left', 'Bottom': 'top', 'Top': 'bottom'}
Opposite = {'Left': 'Right', 'Right': 'Left', 'Bottom': 'Top', 'Top': 'Bottom', 'left': 'Right', 'right': 'Left', 'bottom': 'Top', 'top': 'Bottom'}


class AxisAdjustableCanvas(AxisRangeRightClickCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.axisChanged.connect(self.OnAxisChanged)

    def OnAxisChanged(self, axis):
        if self.axisIsValid('Right'):
            self.setMirrorAxis('Left', False)
            self.setMirrorAxis('Right', False)
        if self.axisIsValid('Top'):
            self.setMirrorAxis('Bottom', False)
            self.setMirrorAxis('Top', False)
        self._emitAxisSelected()

    def SaveAsDictionary(self, dictionary, path):
        super().SaveAsDictionary(dictionary, path)
        dic = {}
        for l in ['Left', 'Right', 'Top', 'Bottom']:
            if self.axisIsValid(l):
                dic[l + "_mode"] = self.getAxisMode(l)
                dic[l + "_mirror"] = self.getMirrorAxis(l)
                dic[l + "_color"] = self.getAxisColor(l)
                dic[l + "_thick"] = self.getAxisThick(l)
            else:
                dic[l + "_mode"] = None
                dic[l + "_mirror"] = None
                dic[l + "_color"] = None
                dic[l + "_thick"] = None

        dictionary['AxisSetting'] = dic

    def LoadFromDictionary(self, dictionary, path):
        super().LoadFromDictionary(dictionary, path)
        if 'AxisSetting' in dictionary:
            dic = dictionary['AxisSetting']
            for l in ['Left', 'Right', 'Top', 'Bottom']:
                if self.axisIsValid(l):
                    self.setAxisMode(l, dic[l + "_mode"])
                    self.setMirrorAxis(l, dic[l + "_mirror"])
                    self.setAxisColor(l, dic[l + "_color"])
                    self.setAxisThick(l, dic[l + "_thick"])

    def _getAxisList(self, axis):
        res = [self.fig.axes[axis.lower()]['item']]
        if not self.axisIsValid(Opposite[axis]):
            res.append(self.fig.axes[opposite[axis]]['item'])
        return res

    @saveCanvas
    def setAxisMode(self, axis, mod):
        ax = self._getAxisList(axis)
        for a in ax:
            if mod == 'log':
                a.setLogMode(True)
            else:
                a.setLogMode(False)

    def getAxisMode(self, axis):
        ax = self.fig.axes[axis.lower()]['item']
        if ax.logMode:
            return 'log'
        else:
            return 'linear'

    @saveCanvas
    def setAxisThick(self, axis, thick):
        ax = self._getAxisList(axis)
        for a in ax:
            pen = a.pen()
            pen.setWidth(thick)
            a.setPen(pen)

    def getAxisThick(self, axis):
        ax = self.fig.axes[axis.lower()]['item']
        return ax.pen().width()

    @saveCanvas
    def setAxisColor(self, axis, color):
        ax = self._getAxisList(axis)
        for a in ax:
            pen = a.pen()
            if isinstance(color, tuple):
                col = [c * 255 for c in color]
                pen.setColor(QColor(*col))
            else:
                pen.setColor(QColor(color))
            a.setPen(pen)

    def getAxisColor(self, axis):
        ax = self.fig.axes[axis.lower()]['item']
        return ax.pen().color().name()

    @saveCanvas
    def setMirrorAxis(self, axis, value):
        ax = self.fig.axes[opposite[axis]]['item']
        ax.setVisible(value)

    def getMirrorAxis(self, axis):
        ax = self.fig.axes[opposite[axis]]['item']
        return ax.isVisible()


class TickAdjustableCanvas(AxisAdjustableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.__data = {}
        self._direction = {'Left': -1, 'Right': -1, 'Top': -1, 'Bottom': -1}
        self._length = {'Left': 5, 'Right': 5, 'Top': 5, 'Bottom': 5}
        self._major = {'Left': 0, 'Right': 0, 'Top': 0, 'Bottom': 0}
        self._minor = {'Left': 0, 'Right': 0, 'Top': 0, 'Bottom': 0}
        self._major_visible = {'Left': True, 'Right': True, 'Top': True, 'Bottom': True}
        self._minor_visible = {'Left': True, 'Right': True, 'Top': True, 'Bottom': True}
        self.setTickDirection('Left', 'in')
        self.setTickDirection('Bottom', 'in')
        self.setTickVisible('Left', False, which='minor')
        self.setTickVisible('Bottom', False, which='minor')
        self.axisRangeChanged.connect(self._refreshTicks)
        self.dataChanged.connect(self._refreshTicks)

    def SaveAsDictionary(self, dictionary, path):
        super().SaveAsDictionary(dictionary, path)
        dic = {}
        for l in ['Left', 'Right', 'Top', 'Bottom']:
            if self.axisIsValid(l):
                dic[l + "_major_on"] = self.getTickVisible(l, mirror=False, which='major')
                dic[l + "_majorm_on"] = self.getTickVisible(l, mirror=True, which='major')
                dic[l + "_ticklen"] = self.getTickLength(l)
                dic[l + "_tickwid"] = self.getTickWidth(l)
                dic[l + "_ticknum"] = self.getAutoLocator(l)
                dic[l + "_minor_on"] = self.getTickVisible(l, mirror=False, which='minor')
                dic[l + "_minorm_on"] = self.getTickVisible(l, mirror=True, which='minor')
                dic[l + "_ticklen2"] = self.getTickLength(l, which='minor')
                dic[l + "_tickwid2"] = self.getTickWidth(l, which='minor')
                dic[l + "_ticknum2"] = self.getAutoLocator(l, which='minor')
                dic[l + "_tickdir"] = self.getTickDirection(l)
        dictionary['TickSetting'] = dic

    def LoadFromDictionary(self, dictionary, path):
        super().LoadFromDictionary(dictionary, path)
        if 'TickSetting' in dictionary:
            dic = dictionary['TickSetting']
            for l in ['Left', 'Right', 'Top', 'Bottom']:
                if self.axisIsValid(l):
                    self.setTickVisible(l, dic[l + "_major_on"], mirror=False, which='major')
                    self.setTickVisible(l, dic[l + "_majorm_on"], mirror=True, which='major')
                    self.setTickLength(l, dic[l + "_ticklen"])
                    self.setTickWidth(l, dic[l + "_tickwid"])
                    self.setAutoLocator(l, dic[l + "_ticknum"])
                    self.setTickVisible(l, dic[l + "_minor_on"], mirror=False, which='minor')
                    self.setTickVisible(l, dic[l + "_minorm_on"], mirror=True, which='minor')
                    self.setTickLength(l, dic[l + "_ticklen2"], which='minor')
                    self.setTickWidth(l, dic[l + "_tickwid2"], which='minor')
                    self.setAutoLocator(l, dic[l + "_ticknum2"], which='minor')
                    self.setTickDirection(l, dic[l + "_tickdir"])

    def _refreshTicks(self):
        for l in ['Left', 'Right', 'Top', 'Bottom']:
            for t in ['major', 'minor']:
                self.setAutoLocator(l, self.getAutoLocator(l, t), t)

    def __alist(self, axis):
        res = [axis]
        if not self.axisIsValid(Opposite[axis]):
            res.append(Opposite[axis])
        return res

    def __set(self):
        for axis in ['Left', 'Right', 'Bottom', 'Top']:
            ax = self.fig.axes[axis.lower()]['item']
            if self._major_visible[axis]:
                ax.setStyle(tickLength=self._direction[axis] * self._length[axis])
            else:
                ax.setStyle(tickLength=0)

    @saveCanvas
    def setAutoLocator(self, axis, n, which='major'):
        self._setAutoLocator(axis, n, which)
        if not self.axisIsValid(Opposite[axis]):
            self._setAutoLocator(Opposite[axis], n, which)

    def _setAutoLocator(self, axis, n, which='major'):
        ax = self.fig.axes[axis.lower()]['item']
        range = self.getAxisRange(axis)
        dr = range[1] - range[0]
        if which == 'major':
            self._major[axis] = n
            if self._minor_visible[axis]:
                if self._minor[axis] == 0:
                    # major: auto, minor: auto
                    if n == 0:
                        ax.setTickSpacing()
                    # major: n, minor: auto
                    else:
                        if dr / n < 100:
                            ax.setTickSpacing(major=n, minor=n / 5)
                        else:
                            ax.setTickSpacing()
                else:
                    # major:auto, minor, specified
                    if n == 0:
                        if dr / (self._minor[axis] * 5) < 100:
                            ax.setTickSpacing(major=self._minor[axis] * 5, minor=self._minor[axis])
                        else:
                            ax.setTickSpacing()
                    # major:n, minor: specified
                    else:
                        if dr / n < 100:
                            ax.setTickSpacing(major=n, minor=self._minor[axis])
                        else:
                            ax.setTickSpacing(major=self._minor[axis] * 5, minor=self._minor[axis])
            else:
                if n == 0 or dr / n >= 100:
                    ax.setTickSpacing()
                    space = ax.tickSpacing(*self.getAxisRange(axis), 100)
                    if space is not None:
                        n = space[1][0] / 5
                    else:
                        n = 5
                    ax.setTickSpacing(levels=[(n, 0)])
                else:
                    ax.setTickSpacing(levels=[(n, 0)])
        else:
            self._minor[axis] = n
            if not self._minor_visible[axis]:
                return
            if self._major[axis] == 0:
                if n == 0:
                    ax.setTickSpacing()
                else:
                    if dr / (n * 5) < 100:
                        ax.setTickSpacing(major=n * 5, minor=n)
                    else:
                        ax.setTickSpacing()
            else:
                if n == 0:
                    if dr / self._major[axis] < 100:
                        ax.setTickSpacing(major=self._major[axis], minor=self._major[axis] / 5)
                    else:
                        ax.setTickSpacing()
                else:
                    if dr / n < 500:
                        ax.setTickSpacing(major=self._major[axis], minor=n)
                    else:
                        ax.setTickSpacing(major=self._major[axis], minor=self._major[axis] / 5)

    def getAutoLocator(self, axis, which='major'):
        if which == 'major':
            return self._major[axis]
        else:
            return self._minor[axis]

    @saveCanvas
    def setTickDirection(self, axis, direction):
        data = {"in": -1, "out": 1}
        for a in self.__alist(axis):
            self._direction[a] = data[direction]
        self.__set()

    def getTickDirection(self, axis):
        if self._direction[axis] > 0:
            return 'out'
        else:
            return 'in'

    @saveCanvas
    def setTickWidth(self, axis, value, which='major'):
        self.setAxisThick(axis, value)

    def getTickWidth(self, axis, which='major'):
        return self.getAxisThick(axis)

    @saveCanvas
    def setTickLength(self, axis, value, which='major'):
        for a in self.__alist(axis):
            self._length[a] = int(value)
        self.__set()

    def getTickLength(self, axis, which='major'):
        return self._length[axis]

    @saveCanvas
    def setTickVisible(self, axis, tf, mirror=False, which='both'):
        if which in ['both', 'major']:
            if not mirror:
                self._major_visible[axis] = tf
            else:
                self._major_visible[Opposite[axis]] = tf
        if which in ['both', 'minor']:
            if not mirror:
                self._minor_visible[axis] = tf
                self._setAutoLocator(axis, self._major[axis], 'major')
            else:
                self._minor_visible[Opposite[axis]] = tf
                self._setAutoLocator(Opposite[axis], self._major[axis], 'major')
        self.__set()

    def getTickVisible(self, axis, mirror=False, which='major'):
        if which == 'major':
            return self._major_visible[axis]
        else:
            return self._minor_visible[axis]
