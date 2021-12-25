#!/usr/bin/env python
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import ticker

from lys import *
from .VectorSettings import *
from ..CanvasInterface import CanvasAxes, CanvasTicks

opposite = {'Left': 'right', 'Right': 'left', 'Bottom': 'top', 'Top': 'bottom'}
Opposite = {'Left': 'Right', 'Right': 'Left', 'Bottom': 'Top', 'Top': 'Bottom'}


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


class _MatplotlibAxes(CanvasAxes):
    def _isValid(self, axis):
        return self.canvas().getAxes(axis) is not None

    def _setRange(self, axis, range):
        axes = self.canvas().getAxes(axis)
        if axis in ['Left', 'Right']:
            axes.set_ylim(range)
        if axis in ['Top', 'Bottom']:
            axes.set_xlim(range)

    def _setAxisThick(self, axis, thick):
        axes = self.canvas().getAxes(axis)
        axes.spines[axis.lower()].set_linewidth(thick)
        axes.spines[opposite[axis]].set_linewidth(thick)

    def _setAxisColor(self, axis, color):
        axes = self.canvas().getAxes(axis)
        axes.spines[axis.lower()].set_edgecolor(color)
        axes.spines[opposite[axis]].set_edgecolor(color)
        if axis in ['Left', 'Right']:
            axes.get_yaxis().set_tick_params(color=color, which='both')
        if axis in ['Top', 'Bottom']:
            axes.get_xaxis().set_tick_params(color=color, which='both')

    def _setMirrorAxis(self, axis, value):
        self.canvas().getAxes(axis).spines[opposite[axis]].set_visible(value)

    def _setAxisMode(self, axis, mod):
        axes = self.canvas().getAxes(axis)
        if axis in ['Left', 'Right']:
            axes.set_yscale(mod)
        else:
            axes.set_xscale(mod)


class _MatplotlibTicks(CanvasTicks):
    def _setTickWidth(self, axis, value, which):
        axes = self.canvas().getAxes(axis)
        if axis in ['Left', 'Right']:
            axes.get_yaxis().set_tick_params(width=value, which=which)
        if axis in ['Top', 'Bottom']:
            axes.get_xaxis().set_tick_params(width=value, which=which)

    def _setTickLength(self, axis, value, which):
        axes = self.canvas().getAxes(axis)
        if axis in ['Left', 'Right']:
            axes.get_yaxis().set_tick_params(length=value, which=which)
        if axis in ['Top', 'Bottom']:
            axes.get_xaxis().set_tick_params(length=value, which=which)

    def _setTickInterval(self, axis, interval, which='major'):
        axs = self.canvas().getAxes(axis)
        loc = ticker.MultipleLocator(interval)
        if axis in ['Left', 'Right']:
            ax = axs.get_yaxis()
        if axis in ['Bottom', 'Top']:
            ax = axs.get_xaxis()
        if which == 'major':
            ax.set_major_locator(loc)
        elif which == 'minor':
            ax.set_minor_locator(loc)

    def _setTickVisible(self, axis, tf, mirror, which='both'):
        axes = self.canvas().getAxes(axis)
        if (axis == 'Left' and not mirror) or (axis == 'Right' and mirror):
            axes.get_yaxis().set_tick_params(left=tf, which=which)
        if (axis == 'Right' and not mirror) or (axis == 'Left' and mirror):
            axes.get_yaxis().set_tick_params(right=tf, which=which)
        if (axis == 'Top' and not mirror) or (axis == 'Bottom' and mirror):
            axes.get_xaxis().set_tick_params(top=tf, which=which)
        if (axis == 'Bottom' and not mirror) or (axis == 'Top' and mirror):
            axes.get_xaxis().set_tick_params(bottom=tf, which=which)

    def _setTickDirection(self, axis, direction):
        axes = self.canvas().getAxes(axis)
        if axis in ['Left', 'Right']:
            axes.get_yaxis().set_tick_params(direction=direction, which='both')
        if axis in ['Top', 'Bottom']:
            axes.get_xaxis().set_tick_params(direction=direction, which='both')


class AxesCanvas(RangeSelectableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self._axs = _MatplotlibAxes(self)
        self._ticks = _MatplotlibTicks(self)

    def __getattr__(self, key):
        if "_axs" in self.__dict__:
            if hasattr(self._axs, key):
                return getattr(self._axs, key)
        if "_ticks" in self.__dict__:
            if hasattr(self._ticks, key):
                return getattr(self._ticks, key)
        return super().__getattr__(key)


class AxisRangeRightClickCanvas(AxesCanvas):
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

    @saveCanvas
    def onScroll(self, event):
        region = self.__FindRegion(event.x, event.y)
        if region == "OnGraph":
            self.__ExpandGraph(event.x, event.y, "Bottom", event.step)
            self.__ExpandGraph(event.x, event.y, "Left", event.step)
        elif not region == "OutOfFigure":
            self.__ExpandGraph(event.x, event.y, region, event.step)

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
            self.setAxisRange('Bottom', [cent - (cent - old[0]) * ratio, cent + (old[1] - cent) * ratio])
        if axis in {"Left"}:
            old = self.getAxisRange('Left')
            cent = (old[1] - old[0]) * loc[1] + old[0]
            self.setAxisRange('Left', [cent - (cent - old[0]) * ratio, cent + (old[1] - cent) * ratio])
        if axis in {"Right", "Left"} and self.axisIsValid('Right'):
            old = self.getAxisRange('Right')
            cent = (old[1] - old[0]) * loc[1] + old[0]
            self.setAxisRange('Right', [cent - (cent - old[0]) * ratio, cent + (old[1] - cent) * ratio])
        if axis in {"Top", "Bottom"} and self.axisIsValid('Top'):
            old = self.getAxisRange('Top')
            cent = (old[1] - old[0]) * loc[0] + old[0]
            self.setAxisRange('Top', [cent - (cent - old[0]) * ratio, cent + (old[1] - cent) * ratio])

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


class TickAdjustableCanvas(AxisRangeScrollableCanvas):
    pass
