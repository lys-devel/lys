#!/usr/bin/env python
import random
import weakref
import sys
import os
import numpy as np
from enum import Enum
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure, SubplotParams
import matplotlib as mpl
import matplotlib.font_manager as fm
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import lines, markers, ticker

from ExtendAnalysis import *
from .VectorSettings import *


class RangeSelectableCanvas(VectorSettingCanvas):
    selectedRangeChanged = pyqtSignal(object)

    def __init__(self, dpi=100):
        super().__init__(dpi)
        self.__rect = Rectangle((0, 0), 0, 0, color='orange', alpha=0.5)
        patch = self.axes.add_patch(self.__rect)
        patch.set_zorder(20000)
        self.Selection = False
        self.rect_pos_start = [0, 0]
        self.rect_pos_end = [0, 0]
        self.mpl_connect('button_press_event', self.OnMouseDown)
        self.mpl_connect('button_release_event', self.OnMouseUp)
        self.mpl_connect('motion_notify_event', self.OnMouseMove)

    def __GlobalToAxis(self, x, y, ax):
        loc = self.__GlobalToRatio(x, y, ax)
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        x_ax = xlim[0] + (xlim[1] - xlim[0]) * loc[0]
        y_ax = ylim[0] + (ylim[1] - ylim[0]) * loc[1]
        return [x_ax, y_ax]

    def __GlobalToRatio(self, x, y, ax):
        ran = ax.get_position()
        x_loc = (x - ran.x0 * self.width()) / ((ran.x1 - ran.x0) * self.width())
        y_loc = (y - ran.y0 * self.height()) / ((ran.y1 - ran.y0) * self.height())
        return [x_loc, y_loc]

    def OnMouseDown(self, event):
        if event.button == 1:
            self.Selection = True
            self.__saved = self.copy_from_bbox(self.axes.bbox)
            self.rect_pos_start = [event.x, event.y]
            self.rect_pos_end = [event.x, event.y]
            ax = self.__GlobalToAxis(event.x, event.y, self.axes)
            self.__rect.set_xy(ax)

    def OnMouseUp(self, event):
        if self.Selection == True and event.button == 1:
            self.rect_pos_end = [event.x, event.y]
            ax = self.__GlobalToAxis(event.x, event.y, self.axes)
            self.__rect.set_width(ax[0] - self.__rect.xy[0])
            self.__rect.set_height(ax[1] - self.__rect.xy[1])
            self.draw()
            self.selectedRangeChanged.emit(self.SelectedRange())
            self.Selection = False

    def OnMouseMove(self, event):
        if self.Selection == True:
            ax = self.__GlobalToAxis(event.x, event.y, self.axes)
            self.__rect.set_width(ax[0] - self.__rect.xy[0])
            self.__rect.set_height(ax[1] - self.__rect.xy[1])
            self.restore_region(self.__saved)
            self.axes.draw_artist(self.__rect)
            self.blit(self.axes.bbox)
            self.selectedRangeChanged.emit(self.SelectedRange())
            self.flush_events()

    def IsRangeSelected(self):
        return not self.__rect.get_width() == 0

    def ClearSelectedRange(self):
        self.__rect.set_width(0)
        self.__rect.set_height(0)

    def SelectedRange(self):
        start = self.__GlobalToAxis(self.rect_pos_start[0], self.rect_pos_start[1], self.axes)
        end = self.__GlobalToAxis(self.rect_pos_end[0], self.rect_pos_end[1], self.axes)
        if start[0] == end[0] and start[1] == end[1]:
            return None
        else:
            return (start, end)


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
        self.__auto = {"Left": True, "Right": True, "Top": True, "Bottom": True}

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
    def setAxisRange(self, range, axis, auto=False):
        ax = axis
        axes = self.getAxes(axis)
        if axes is None:
            return
        if ax in ['Left', 'Right']:
            axes.set_ylim(range)
        if ax in ['Top', 'Bottom']:
            axes.set_xlim(range)
        if not auto:
            self.__auto[axis] = False
        self.axisRangeChanged.emit()

    def getAxisRange(self, axis):
        ax = axis
        axes = self.getAxes(axis)
        if axes is None:
            return
        if ax in ['Left', 'Right']:
            return axes.get_ylim()
        if ax in ['Top', 'Bottom']:
            return axes.get_xlim()

    @saveCanvas
    def setAutoScaleAxis(self, axis):
        ax = axis
        axes = self.getAxes(axis=ax)
        if axes is None:
            return
        max = np.NaN
        min = np.NaN
        with np.errstate(invalid='ignore'):
            if ax in ['Left', 'Right']:
                for l in self.getLines():
                    max = np.nanmax([*l.wave.data, max])
                    min = np.nanmin([*l.wave.data, min])
                for im in self.getImages():
                    max = np.nanmax([*im.wave.y, max])
                    min = np.nanmin([*im.wave.y, min])
            if ax in ['Top', 'Bottom']:
                for l in self.getLines():
                    max = np.nanmax([*l.wave.x, max])
                    min = np.nanmin([*l.wave.x, min])
                for im in self.getImages():
                    max = np.nanmax([*im.wave.x, max])
                    min = np.nanmin([*im.wave.x, min])
        if np.isnan(max) or np.isnan(min):
            return
        if len(self.getImages()) == 0:
            mergin = (max - min) / 20
        else:
            mergin = 0
        r = self.getAxisRange(axis)
        if r[0] < r[1]:
            self.setAxisRange([min - mergin, max + mergin], axis, auto=True)
        else:
            self.setAxisRange([max + mergin, min - mergin], axis, auto=True)
        self.__auto[axis] = True

    def isAutoScaled(self, axis):
        ax = axis
        axes = self.getAxes(axis=ax)
        if axes is None:
            return
        else:
            return self.__auto[axis]
        if ax in ['Left', 'Right']:
            return axes.get_autoscaley_on()
        if ax in ['Top', 'Bottom']:
            return axes.get_autoscalex_on()


class AxisRangeRightClickCanvas(AxisRangeAdjustableCanvas):
    def __GlobalToAxis(self, x, y, ax):
        loc = self.__GlobalToRatio(x, y, ax)
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        x_ax = xlim[0] + (xlim[1] - xlim[0]) * loc[0]
        y_ax = ylim[0] + (ylim[1] - ylim[0]) * loc[1]
        return [x_ax, y_ax]

    def __GlobalToRatio(self, x, y, ax):
        ran = ax.get_position()
        x_loc = (x - ran.x0 * self.width()) / ((ran.x1 - ran.x0) * self.width())
        y_loc = (y - ran.y0 * self.height()) / ((ran.y1 - ran.y0) * self.height())
        return [x_loc, y_loc]

    @saveCanvas
    def __ExpandAndShrink(self, mode, axis):
        if not self.axisIsValid(axis):
            return
        ax = self.getAxes(axis)
        pos = self.__GlobalToAxis(self.rect_pos_start[0], self.rect_pos_start[1], ax)
        pos2 = self.__GlobalToAxis(self.rect_pos_end[0], self.rect_pos_end[1], ax)
        width = pos2[0] - pos[0]
        height = pos2[1] - pos[1]
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

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
        self.draw()

    def __auto(self):
        for axis in ['Left', 'Right', 'Bottom', 'Top']:
            self.setAutoScaleAxis(axis)
        self.ClearSelectedRange()
        self.draw()


class AxisRangeScrollableCanvas(AxisRangeRightClickCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi)
        self.mpl_connect('scroll_event', self.onScroll)

    def onScroll(self, event):
        region = self.__FindRegion(event.x, event.y)
        if region == "OnGraph":
            self.__ExpandGraph(event.x, event.y, "Bottom", event.step)
            self.__ExpandGraph(event.x, event.y, "Left", event.step)
        elif not region == "OutOfFigure":
            self.__ExpandGraph(event.x, event.y, region, event.step)
        self.draw()

    def __GlobalToAxis(self, x, y, ax):
        loc = self.__GlobalToRatio(x, y, ax)
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        x_ax = xlim[0] + (xlim[1] - xlim[0]) * loc[0]
        y_ax = ylim[0] + (ylim[1] - ylim[0]) * loc[1]
        return [x_ax, y_ax]

    def __GlobalToRatio(self, x, y, ax):
        ran = ax.get_position()
        x_loc = (x - ran.x0 * self.width()) / ((ran.x1 - ran.x0) * self.width())
        y_loc = (y - ran.y0 * self.height()) / ((ran.y1 - ran.y0) * self.height())
        return [x_loc, y_loc]

    def __ExpandGraph(self, x, y, axis, step):
        ratio = 1.05**step
        loc = self.__GlobalToRatio(x, y, self.axes)
        if axis in {"Bottom"}:
            old = self.getAxisRange('Bottom')
            cent = (old[1] - old[0]) * loc[0] + old[0]
            self.setAxisRange([cent - (cent - old[0]) * ratio, cent + (old[1] - cent) * ratio], 'Bottom')
        if axis in {"Left"}:
            old = self.getAxisRange('Left')
            cent = (old[1] - old[0]) * loc[1] + old[0]
            self.setAxisRange([cent - (cent - old[0]) * ratio, cent + (old[1] - cent) * ratio], 'Left')
        if axis in {"Right", "Left"} and self.axisIsValid('Right'):
            old = self.getAxisRange('Right')
            cent = (old[1] - old[0]) * loc[1] + old[0]
            self.setAxisRange([cent - (cent - old[0]) * ratio, cent + (old[1] - cent) * ratio], 'Right')
        if axis in {"Top", "Bottom"} and self.axisIsValid('Top'):
            old = self.getAxisRange('Top')
            cent = (old[1] - old[0]) * loc[0] + old[0]
            self.setAxisRange([cent - (cent - old[0]) * ratio, cent + (old[1] - cent) * ratio], 'Top')

    def __FindRegion(self, x, y):
        ran = self.axes.get_position()
        x_loc = x / self.width()
        y_loc = y / self.height()
        pos_mode = "OutOfFigure"
        if x_loc < 0 or y_loc < 0 or x_loc > 1 or y_loc > 1:
            pos_mode = "OutOfFigure"
        elif x_loc < ran.x0:
            if ran.y0 < y_loc and y_loc < ran.y1:
                pos_mode = "Left"
        elif x_loc > ran.x1:
            if ran.y0 < y_loc and y_loc < ran.y1:
                pos_mode = "Right"
        elif y_loc < ran.y0:
            pos_mode = "Bottom"
        elif y_loc > ran.y1:
            pos_mode = "Top"
        else:
            pos_mode = "OnGraph"
        return pos_mode


opposite = {'Left': 'right', 'Right': 'left', 'Bottom': 'top', 'Top': 'bottom'}
Opposite = {'Left': 'Right', 'Right': 'Left', 'Bottom': 'Top', 'Top': 'Bottom'}


class AxisAdjustableCanvas(AxisRangeScrollableCanvas):
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

    @saveCanvas
    def setAxisMode(self, axis, mod):
        axes = self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left', 'Right']:
            axes.set_yscale(mod)
        else:
            axes.set_xscale(mod)
        axes.minorticks_on()
        self.draw()

    def getAxisMode(self, axis):
        axes = self.getAxes(axis)
        if axis in ['Left', 'Right']:
            return axes.get_yscale()
        else:
            return axes.get_xscale()

    @saveCanvas
    def setAxisThick(self, axis, thick):
        axes = self.getAxes(axis)
        if axes is None:
            return
        axes.spines[axis.lower()].set_linewidth(thick)
        axes.spines[opposite[axis]].set_linewidth(thick)
        self.draw()

    def getAxisThick(self, axis):
        axes = self.getAxes(axis)
        return axes.spines[axis.lower()].get_linewidth()

    @saveCanvas
    def setAxisColor(self, axis, color):
        axes = self.getAxes(axis)
        if axes is None:
            return
        axes.spines[axis.lower()].set_edgecolor(color)
        axes.spines[opposite[axis]].set_edgecolor(color)
        if axis in ['Left', 'Right']:
            axes.get_yaxis().set_tick_params(color=color, which='both')
        if axis in ['Top', 'Bottom']:
            axes.get_xaxis().set_tick_params(color=color, which='both')
        self.draw()

    def getAxisColor(self, axis):
        axes = self.getAxes(axis)
        color = axes.spines[axis.lower()].get_edgecolor()
        return color

    @saveCanvas
    def setMirrorAxis(self, axis, value):
        axes = self.getAxes(axis)
        if axes is None:
            return
        axes.spines[opposite[axis]].set_visible(value)
        self.draw()

    def getMirrorAxis(self, axis):
        axes = self.getAxes(axis)
        if axes is None:
            return
        return axes.spines[opposite[axis]].get_visible()


class TickAdjustableCanvas(AxisAdjustableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.__data = {}
        self.setTickDirection('Left', 'in')
        self.setTickDirection('Bottom', 'in')
        self.setTickVisible('Left', False, which='minor')
        self.setTickVisible('Bottom', False, which='minor')
        self.axisRangeChanged.connect(self._refreshTicks)
        self.dataChanged.connect(self._refreshTicks)

    def _refreshTicks(self):
        for l in ['Left', 'Right', 'Top', 'Bottom']:
            for t in ['major', 'minor']:
                try:
                    self.setAutoLocator(l, self.getAutoLocator(l, t), t)
                except:
                    pass

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

    @saveCanvas
    def setAutoLocator(self, axis, n, which='major'):
        axs = self.getAxes(axis)
        if axs is None:
            return
        if n == 0:
            loc = ticker.AutoLocator()
        else:
            range = self.getAxisRange(axis)
            if (abs(range[1] - range[0]) / n) < 100:
                loc = ticker.MultipleLocator(n)
            else:
                loc = ticker.AutoLocator()
        if axis in ['Left', 'Right']:
            ax = axs.get_yaxis()
        if axis in ['Bottom', 'Top']:
            ax = axs.get_xaxis()
        if which == 'major':
            ax.set_major_locator(loc)
        elif which == 'minor':
            ax.set_minor_locator(loc)

    def getAutoLocator(self, axis, which='major'):
        axes = self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left', 'Right']:
            ax = axes.get_yaxis()
        if axis in ['Bottom', 'Top']:
            ax = axes.get_xaxis()
        if which == 'major':
            l = ax.get_major_locator()
        elif which == 'minor':
            l = ax.get_minor_locator()
        if isinstance(l, ticker.AutoLocator):
            return 0
        else:
            try:
                return l()[1] - l()[0]
            except:
                return 0

    @saveCanvas
    def setTickDirection(self, axis, direction):
        axes = self.getAxes(axis)
        if axes == None:
            return
        if axis in ['Left', 'Right']:
            axes.get_yaxis().set_tick_params(direction=direction, which='both')
        if axis in ['Top', 'Bottom']:
            axes.get_xaxis().set_tick_params(direction=direction, which='both')

    def getTickDirection(self, axis):
        data = ['in', 'out', 'inout']
        marker = self._getTickLine(axis, 'major').get_marker()
        if axis == 'Left':
            list = [1, 0, '_']
        if axis == 'Right':
            list = [0, 1, '_']
        elif axis == 'Bottom':
            list = [2, 3, '|']
        elif axis == 'Top':
            list = [3, 2, '|']
        return data[list.index(marker)]

    @saveCanvas
    def setTickWidth(self, axis, value, which='major'):
        axes = self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left', 'Right']:
            axes.get_yaxis().set_tick_params(width=value, which=which)
        if axis in ['Top', 'Bottom']:
            axes.get_xaxis().set_tick_params(width=value, which=which)
        self.draw()

    def getTickWidth(self, axis, which='major'):
        return self._getTickLine(axis, which).get_markeredgewidth()

    @saveCanvas
    def setTickLength(self, axis, value, which='major'):
        axes = self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left', 'Right']:
            axes.get_yaxis().set_tick_params(length=value, which=which)
        if axis in ['Top', 'Bottom']:
            axes.get_xaxis().set_tick_params(length=value, which=which)
        self.draw()

    def getTickLength(self, axis, which='major'):
        return self._getTickLine(axis, which).get_markersize()

    def _getTickLine(self, axis, which):
        axs = self.getAxes(axis)
        if axis in ['Left', 'Right']:
            ax = axs.get_yaxis()
        if axis in ['Bottom', 'Top']:
            ax = axs.get_xaxis()
        if which == 'major':
            tick = ax.get_major_ticks()[0]
        elif which == 'minor':
            ticks = ax.get_minor_ticks()
            if len(ticks) == 0:
                tick = ax.get_major_ticks()[0]
            else:
                tick = ticks[0]
        if axis in ['Left', 'Bottom']:
            return tick.tick1line
        else:
            return tick.tick2line

    @saveCanvas
    def setTickVisible(self, axis, tf, mirror=False, which='both'):
        axes = self.getAxes(axis)
        if axes == None:
            return
        if (axis == 'Left' and not mirror) or (axis == 'Right' and mirror):
            axes.get_yaxis().set_tick_params(left=tf, which=which)
        if (axis == 'Right' and not mirror) or (axis == 'Left' and mirror):
            axes.get_yaxis().set_tick_params(right=tf, which=which)
        if (axis == 'Top' and not mirror) or (axis == 'Bottom' and mirror):
            axes.get_xaxis().set_tick_params(top=tf, which=which)
        if (axis == 'Bottom' and not mirror) or (axis == 'Top' and mirror):
            axes.get_xaxis().set_tick_params(bottom=tf, which=which)
        self.draw()

    def getTickVisible(self, axis, mirror=False, which='major'):
        axs = self.getAxes(axis)
        if axis in ['Left', 'Right']:
            ax = axs.get_yaxis()
        if axis in ['Bottom', 'Top']:
            ax = axs.get_xaxis()
        if which == 'major':
            tick = ax.get_major_ticks()[0]
        elif which == 'minor':
            ticks = ax.get_minor_ticks()
            if len(ticks) == 0:
                tick = ax.get_major_ticks()[0]
            else:
                tick = ticks[0]
        if axis in ['Left', 'Bottom']:
            if mirror:
                res = tick.tick2line.get_visible()  # tick.tick2On
            else:
                res = tick.tick1line.get_visible()  # tick.tick1On
        else:
            if mirror:
                res = tick.tick1line.get_visible()  # tick.tick1On
            else:
                res = tick.tick2line.get_visible()  # tick.tick2On
        if isinstance(res, bool):
            return res
        elif isinstance(res, str):
            return res == "on"
