#!/usr/bin/env python
import warnings
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from lys import *
from lys.errors import NotSupportedWarning
from .CanvasBase import saveCanvas
from .CanvasBase import *

from ..CanvasInterface import CanvasAxes, CanvasTicks

opposite = {'Left': 'right', 'Right': 'left', 'Bottom': 'top', 'Top': 'bottom'}
Opposite = {'Left': 'Right', 'Right': 'Left', 'Bottom': 'Top', 'Top': 'Bottom', 'left': 'Right', 'right': 'Left', 'bottom': 'Top', 'top': 'Bottom'}


class RangeSelectableCanvas(FigureCanvasBase):
    selectedRangeChanged = pyqtSignal(object)

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
                self.selectedRangeChanged.emit(self.SelectedRange())
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


class _pyqtGraphAxes(CanvasAxes):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas().pgRangeChanged.connect(self._rangeChanged)

    def _rangeChanged(self, axis):
        if "Left" in axis and self.axisIsValid("Left"):
            _, yrange = self.canvas().getAxes("Left").viewRange()
            if yrange != self.getAxisRange("Left"):
                self.setAxisRange("Left", yrange)
        if "Right" in axis and self.axisIsValid("Right"):
            _, yrange = self.canvas().getAxes("Right").viewRange()
            if yrange != self.getAxisRange("Right"):
                self.setAxisRange("Right", yrange)
        if "Bottom" in axis and self.axisIsValid("Bottom"):
            xrange, _ = self.canvas().getAxes("Bottom").viewRange()
            if xrange != self.getAxisRange("Bottom"):
                self.setAxisRange("Bottom", xrange)
        if "Top" in axis and self.axisIsValid("Top"):
            xrange, _ = self.canvas().getAxes("Top").viewRange()
            if xrange != self.getAxisRange("Top"):
                self.setAxisRange("Top", xrange)

    def _isValid(self, axis):
        return self.canvas().getAxes(axis) is not None

    def _setRange(self, axis, range):
        axes = self.canvas().getAxes(axis)
        if axis in ['Left', 'Right']:
            axes.setYRange(*range, padding=0)
            axes.disableAutoRange(axis='y')
            axes.invertY(range[0] > range[1])
        if axis in ['Top', 'Bottom']:
            axes.setXRange(*range, padding=0)
            axes.disableAutoRange(axis='x')
            axes.invertX(range[0] > range[1])

    def _setAxisThick(self, axis, thick):
        ax = self._getAxisList(axis)
        for a in ax:
            pen = a.pen()
            pen.setWidth(thick)
            c = pen.color()
            if thick == 0:
                c.setAlphaF(0)
            else:
                c.setAlphaF(1)
            pen.setColor(c)
            a.setPen(pen)

    def _setAxisColor(self, axis, color):
        ax = self._getAxisList(axis)
        for a in ax:
            pen = a.pen()
            if isinstance(color, tuple):
                col = [c * 255 for c in color]
                pen.setColor(QColor(*col))
            else:
                pen.setColor(QColor(color))
            a.setPen(pen)

    def _setMirrorAxis(self, axis, value):
        warnings.warn("pyqtGraph does not support show/hide mirror axes.", NotSupportedWarning)

    def _getAxisList(self, axis):
        res = [self.canvas().fig.axes[axis.lower()]['item']]
        if not self.axisIsValid(Opposite[axis]):
            res.append(self.canvas().fig.axes[opposite[axis]]['item'])
        return res

    def _setAxisMode(self, axis, mod):
        if mod == 'log':
            warnings.warn("pyqtGraph does not support log scale.", NotSupportedWarning)


class _pyqtGraphTicks(CanvasTicks):
    def _setTickWidth(self, axis, value, which='major'):
        warnings.warn("pyqtGraph does not support setting width axes. Use axis thick instead.", NotSupportedWarning)

    def __alist(self, axis):
        res = [axis]
        if not self.canvas().axisIsValid(Opposite[axis]):
            res.append(Opposite[axis])
        return res

    def __set(self, axis, visible, direction, length):
        dir = {"in": -1, "out": 1, 1: 1, -1: -1, None: 0}
        direction = dir[direction]
        if visible:
            visible = 1
        else:
            visible = 0
        ax = self.canvas().fig.axes[axis.lower()]['item']
        ax.setStyle(tickLength=int(direction * length * visible))

    def _setTickInterval(self, axis, value, which='major'):
        for ax in self.__alist(axis):
            ax = self.canvas().fig.axes[ax.lower()]['item']
            if which == 'major':
                if self.getTickVisible(axis, which='minor'):
                    ax.setTickSpacing(major=value, minor=self.getTickInterval(axis, which="minor", raw=False))
                else:
                    ax.setTickSpacing(major=value, minor=value)
            elif self.getTickVisible(axis, which='minor'):
                ax.setTickSpacing(major=self.getTickInterval(axis, which="major", raw=False), minor=value)

    def _setTickDirection(self, axis, direction):
        self.__set(axis, self.getTickVisible(axis), direction, self.getTickLength(axis))
        if not self.canvas().axisIsValid(Opposite[axis]):
            self.__set(Opposite[axis], self.getTickVisible(axis, mirror=True), direction, self.getTickLength(axis))

    def _setTickLength(self, axis, value, which='major'):
        if which == 'minor':
            warnings.warn("pyqtGraph does not support setting tick length of minor axes.", NotSupportedWarning)
            return
        self.__set(axis, self.getTickVisible(axis), self.getTickDirection(axis), int(value))
        if not self.canvas().axisIsValid(Opposite[axis]):
            self.__set(Opposite[axis], self.getTickVisible(axis, mirror=True), self.getTickDirection(axis), int(value))

    def _setTickVisible(self, axis, tf, mirror=False, which='both'):
        if which in ['both', 'major']:
            if mirror:
                if not self.canvas().axisIsValid(Opposite[axis]):
                    self.__set(Opposite[axis], tf, self.getTickDirection(axis), self.getTickLength(axis))
            else:
                self.__set(axis, tf, self.getTickDirection(axis), self.getTickLength(axis))
        if which in ['both', 'minor']:
            if tf:
                w = "minor"
            else:
                w = "major"
            if mirror:
                if not self.canvas().axisIsValid(Opposite[axis]):
                    ax = self.canvas().fig.axes[Opposite[axis].lower()]['item']
                    ax.setTickSpacing(major=self.getTickInterval(axis, which="major", raw=False), minor=self.getTickInterval(axis, which=w, raw=False))
            else:
                ax = self.canvas().fig.axes[axis.lower()]['item']
                ax.setTickSpacing(major=self.getTickInterval(axis, which="major", raw=False), minor=self.getTickInterval(axis, which=w, raw=False))


class AxesCanvas(RangeSelectableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self._axs = _pyqtGraphAxes(self)
        self._ticks = _pyqtGraphTicks(self)

    def __getattr__(self, key):
        if "_axs" in self.__dict__:
            if hasattr(self._axs, key):
                return getattr(self._axs, key)
        if "_ticks" in self.__dict__:
            if hasattr(self._ticks, key):
                return getattr(self._ticks, key)
        return super().__getattr__(key)


class AxisRangeRightClickCanvas(AxesCanvas):
    @ saveCanvas
    def __ExpandAndShrink(self, mode, axis):
        if not self.axisIsValid(axis):
            return
        pos, pos2 = self.SelectedRange()
        width = pos2[0] - pos[0]
        height = pos2[1] - pos[1]
        xlim = self.getAxisRange("Bottom")
        ylim = self.getAxisRange("Left")

        if axis in ['Bottom', 'Top']:
            if mode in ['Expand', 'Horizontal Expand']:
                minVal = min(pos[0], pos[0] + width)
                maxVal = max(pos[0], pos[0] + width)
                self.setAxisRange(axis, [minVal, maxVal])
            if mode in ['Shrink', 'Horizontal Shrink']:
                ratio = abs((xlim[1] - xlim[0]) / width)
                a = min(pos[0], pos[0] + width)
                b = max(pos[0], pos[0] + width)
                minVal = xlim[0] - ratio * (a - xlim[0])
                maxVal = xlim[1] + ratio * (xlim[1] - b)
                self.setAxisRange(axis, [minVal, maxVal])
        else:
            if mode in ['Vertical Expand', 'Expand']:
                if ylim[1] < ylim[0]:
                    minVal = max(pos[1], pos[1] + height)
                    maxVal = min(pos[1], pos[1] + height)
                else:
                    minVal = min(pos[1], pos[1] + height)
                    maxVal = max(pos[1], pos[1] + height)
                self.setAxisRange(axis, [minVal, maxVal])
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
                self.setAxisRange(axis, [minVal, maxVal])

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


class TickAdjustableCanvas(AxisRangeRightClickCanvas):
    pass
