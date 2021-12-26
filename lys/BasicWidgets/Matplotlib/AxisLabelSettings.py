from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from lys import *
from .CanvasBase import saveCanvas
from .AxisSettings import *
from ..CanvasInterface import CanvasFont, CanvasAxisLabel, CanvasTickLabel


class _MatplotlibAxisLabel(CanvasAxisLabel):
    def _setAxisLabel(self, axis, text):
        axes = self.canvas().getAxes(axis)
        if axis in ['Left', 'Right']:
            axes.get_yaxis().get_label().set_text(text)
        else:
            axes.get_xaxis().get_label().set_text(text)

    def _setAxisLabelVisible(self, axis, b):
        axes = self.canvas().getAxes(axis)
        if axis in ['Left', 'Right']:
            axes.get_yaxis().get_label().set_visible(b)
        else:
            axes.get_xaxis().get_label().set_visible(b)

    def _setAxisLabelCoords(self, axis, pos):
        axes = self.canvas().getAxes(axis)
        if axis in ['Left', 'Right']:
            axes.get_yaxis().set_label_coords(pos, 0.5)
        else:
            axes.get_xaxis().set_label_coords(0.5, pos)

    def _setAxisLabelFont(self, axis, family, size, color):
        axes = self.canvas().getAxes(axis)
        if axis in ['Left', 'Right']:
            axes.get_yaxis().get_label().set_family(family)
            axes.get_yaxis().get_label().set_size(size)
            axes.get_yaxis().get_label().set_color(color)
        else:
            axes.get_xaxis().get_label().set_family(family)
            axes.get_xaxis().get_label().set_size(size)
            axes.get_xaxis().get_label().set_color(color)


class _MatplotlibTickLabel(CanvasTickLabel):
    pass


class FontSelectableCanvas(TickAdjustableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self._font = CanvasFont(self)
        self._axisLabel = _MatplotlibAxisLabel(self)
        self._tickLabel = _MatplotlibTickLabel(self)

    def __getattr__(self, key):
        if "_font" in self.__dict__:
            if hasattr(self._font, key):
                return getattr(self._font, key)
        if "_axisLabel" in self.__dict__:
            if hasattr(self._axisLabel, key):
                return getattr(self._axisLabel, key)
        if "_tickLabel" in self.__dict__:
            if hasattr(self._tickLabel, key):
                return getattr(self._tickLabel, key)
        return super().__getattr__(key)


class TickLabelAdjustableCanvas(FontSelectableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.fontChanged.connect(self.__onFontChanged)

    def SaveAsDictionary(self, dictionary, path):
        super().SaveAsDictionary(dictionary, path)
        dic = {}
        for l in ['Left', 'Right', 'Top', 'Bottom']:
            if self.axisIsValid(l):
                dic[l + "_label_on"] = self.getTickLabelVisible(l)
                dic[l + "_font"] = self.getTickLabelFont(l).ToDict()
        dictionary['TickLabelSetting'] = dic

    def LoadFromDictionary(self, dictionary, path):
        super().LoadFromDictionary(dictionary, path)
        if 'TickLabelSetting' in dictionary:
            dic = dictionary['TickLabelSetting']
            for l in ['Left', 'Right', 'Top', 'Bottom']:
                if self.axisIsValid(l):
                    self.setTickLabelVisible(l, dic[l + "_label_on"])
                    self.setTickLabelFont(l, FontInfo.FromDict(dic[l + "_font"]))

    def __onFontChanged(self, name):
        for axis in ['Left', 'Right', 'Top', 'Bottom']:
            if self.axisIsValid(axis):
                self.setTickLabelFont(axis, self.getCanvasFont('Tick'))

    @saveCanvas
    def setTickLabelVisible(self, axis, tf, mirror=False, which='both'):
        axes = self.getAxes(axis)
        if axes is None:
            return
        if (axis == 'Left' and not mirror) or (axis == 'Right' and mirror):
            axes.get_yaxis().set_tick_params(labelleft=tf, which=which)
        if (axis == 'Right' and not mirror) or (axis == 'Left' and mirror):
            axes.get_yaxis().set_tick_params(labelright=tf, which=which)
        if (axis == 'Top' and not mirror) or (axis == 'Bottom' and mirror):
            axes.get_xaxis().set_tick_params(labeltop=tf, which=which)
        if (axis == 'Bottom' and not mirror) or (axis == 'Top' and mirror):
            axes.get_xaxis().set_tick_params(labelbottom=tf, which=which)

    def getTickLabelVisible(self, axis, mirror=False, which='major'):
        axs = self.getAxes(axis)
        if axis in ['Left', 'Right']:
            ax = axs.get_yaxis()
        if axis in ['Bottom', 'Top']:
            ax = axs.get_xaxis()
        if which == 'major':
            tick = ax.get_major_ticks()[0]
        elif which == 'minor':
            tick = ax.get_minor_ticks()[0]
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

    @saveCanvas
    def setTickLabelFont(self, axis, font):
        axes = self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left', 'Right']:
            for tick in axes.get_xticklabels():
                tick.set_fontname(font.family)
            axis = 'x'
        else:
            for tick in axes.get_yticklabels():
                tick.set_fontname(font.family)
            axis = 'y'
        axes.tick_params(which='major', labelsize=font.size, color=font.color, axis=axis)
        self.draw()

    def getTickLabelFont(self, axis):
        axes = self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left', 'Right']:
            tick = axes.get_yaxis().get_major_ticks()[0]
        else:
            tick = axes.get_xaxis().get_major_ticks()[0]
        l = tick.label1
        return FontInfo(l.get_family()[0], l.get_size(), l.get_color())


class AxisSettingCanvas(TickLabelAdjustableCanvas):
    pass
