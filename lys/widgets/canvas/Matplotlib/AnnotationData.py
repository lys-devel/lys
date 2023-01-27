import numpy as np
from matplotlib import transforms, patches

from ..interface import CanvasAnnotation, LineAnnotation, InfiniteLineAnnotation, TextAnnotation, RectAnnotation, RegionAnnotation, FreeRegionAnnotation, CrossAnnotation


def _setZ(obj, z):
    obj.set_zorder(z - 100000)


class _MatplotlibLineAnnotation(LineAnnotation):
    def _initialize(self, pos, axis):
        axes = self.canvas().getAxes(axis)
        self._obj, = axes.plot((pos[0][0], pos[1][0]), (pos[0][1], pos[1][1]))
        self._obj.set_pickradius(5)

    def _setPosition(self, pos):
        self._obj.set_data((pos[0][0], pos[1][0]), (pos[0][1], pos[1][1]))

    def _setLineColor(self, color):
        self._obj.set_color(color)

    def _setLineStyle(self, style):
        self._obj.set_linestyle(style)

    def _setLineWidth(self, width):
        self._obj.set_linewidth(width)

    def _setZOrder(self, z):
        _setZ(self._obj, z)

    def _setVisible(self, visible):
        self._obj.set_visible(visible)

    def remove(self):
        self._obj.remove()


class _MatplotlibInfiniteLineAnnotation(InfiniteLineAnnotation):
    """Implementation of InfiniteLineAnnotation for matplotlib"""

    def _initialize(self, pos, orientation, axis):
        self._axis = axis
        self._orientation = orientation
        axes = self.canvas().getAxes(axis)
        if orientation == 'vertical':
            self._obj, = axes.plot((pos, 0), (pos, 0))
        else:
            self._obj, = axes.plot((0, pos), (0, pos))
        self._obj.set_pickradius(5)
        self.canvas().axisRangeChanged.connect(self.__changed)
        self._setPosition(pos)

    def __changed(self):
        self._setPosition(self.getPosition())

    def _setPosition(self, pos):
        xr, yr = self.canvas().getAxisRange(self._axis)
        if self._orientation == 'vertical':
            self._obj.set_data((pos, pos), (min(*yr) - 1, max(*yr) + 1))
        else:
            self._obj.set_data((min(*xr) - 1, max(*xr) + 1), (pos, pos))

    def _setLineColor(self, color):
        self._obj.set_color(color)

    def _setLineStyle(self, style):
        self._obj.set_linestyle(style)

    def _setLineWidth(self, width):
        self._obj.set_linewidth(width)

    def _setZOrder(self, z):
        _setZ(self._obj, z)

    def _setVisible(self, visible):
        self._obj.set_visible(visible)

    def remove(self):
        self._obj.remove()


class _MatplotlibRectAnnotation(RectAnnotation):
    """Implementation of RectAnnotation for matplotlib"""

    def _initialize(self, pos, size, axis):
        self._axes = self.canvas().getAxes(axis)
        self._obj = patches.Rectangle(pos, size[0], size[1], color='magenta', alpha=0.5, transform=self._axes.transData)
        self._patch = self._axes.add_patch(self._obj)

    def _setRegion(self, region):
        self._obj.set_xy((region[0][0], region[1][0]))
        self._obj.set_width(region[0][1] - region[0][0])
        self._obj.set_height(region[1][1] - region[1][0])

    def _setLineColor(self, color):
        self._obj.set_color(color)

    def _setLineStyle(self, style):
        self._obj.set_linestyle(style)

    def _setLineWidth(self, width):
        self._obj.set_linewidth(width)

    def _setZOrder(self, z):
        _setZ(self._obj, z)

    def _setVisible(self, visible):
        self._obj.set_visible(visible)

    def remove(self):
        self._obj.remove()


class _MatplotlibRegionAnnotation(RegionAnnotation):
    """Implementation of RegionAnnotation for matplotlib"""

    def _initialize(self, region, orientation, axis):
        self._orientation = orientation
        self._axis = axis
        self._axes = self.canvas().getAxes(axis)
        self._obj = patches.Rectangle((0, 0), 1, 1, color='magenta', alpha=0.5, transform=self._axes.transData)
        self._patch = self._axes.add_patch(self._obj)
        self._setRegion(region)
        self.canvas().axisRangeChanged.connect(self.__changed)

    def __changed(self):
        self._setRegion(self.getRegion())

    def _setRegion(self, region):
        rx, ry = self.canvas().getAxisRange(self._axis)
        if self._orientation == 'vertical':
            self._obj.set_xy([region[0], ry[0]])
            self._obj.set_width(region[1] - region[0])
            self._obj.set_height(ry[1] - ry[0])
        else:
            self._obj.set_xy([rx[0], region[0]])
            self._obj.set_width(rx[1] - rx[0])
            self._obj.set_height(region[1] - region[0])

    def _setLineColor(self, color):
        self._obj.set_color(color)

    def _setLineStyle(self, style):
        self._obj.set_linestyle(style)

    def _setLineWidth(self, width):
        self._obj.set_linewidth(width)

    def _setZOrder(self, z):
        _setZ(self._obj, z)

    def _setVisible(self, visible):
        self._obj.set_visible(visible)

    def remove(self):
        self._obj.remove()


class _MatplotlibFreeRegionAnnotation(FreeRegionAnnotation):
    """Implementation of FreeRegionAnnotation for matplotlib"""

    def _initialize(self, region, width, axis):
        pos1, pos2 = np.array(region[0]), np.array(region[1])
        d = pos2 - pos1
        v = np.array([-d[1], d[0]])
        pos = pos1 - width * v / np.linalg.norm(v) / 2

        self._axes = self.canvas().getAxes(axis)
        self._obj = patches.Rectangle(pos, np.linalg.norm(d), width, color='magenta', alpha=0.5, transform=self._axes.transData, angle=np.angle(d[0] + 1j * d[1], deg=True),)
        self._patch = self._axes.add_patch(self._obj)

    def _setRegion(self, region):
        pos1, pos2 = np.array(region[0]), np.array(region[1])
        d = pos2 - pos1
        v = np.array([-d[1], d[0]])
        pos = pos1 - self.getWidth() * v / np.linalg.norm(v) / 2
        self._obj.set_xy(pos)
        self._obj.set_width(np.linalg.norm(d))
        self._obj.angle = np.angle(d[0] + 1j * d[1], deg=True)

    def _setWidth(self, width):
        self._obj.set_height(width)
        self._setRegion(self.getRegion())

    def _setLineColor(self, color):
        self._obj.set_color(color)

    def _setLineStyle(self, style):
        self._obj.set_linestyle(style)

    def _setLineWidth(self, width):
        self._obj.set_linewidth(width)

    def _setZOrder(self, z):
        _setZ(self._obj, z)

    def _setVisible(self, visible):
        self._obj.set_visible(visible)

    def remove(self):
        self._obj.remove()


class _MatplotlibCrossAnnotation(CrossAnnotation):
    """Implementation of CrossAnnotation for matplotlib"""

    def _initialize(self, position, axis):
        self._axis = axis
        axes = self.canvas().getAxes(axis)
        self._obj = _CrosshairItem(self.canvas(), axes, position)
        self.canvas().axisRangeChanged.connect(self.__changed)
        self._setPosition(position)

    def __changed(self):
        self._setPosition(self.getPosition())

    def _setPosition(self, pos):
        xr, yr = self.canvas().getAxisRange(self._axis)
        self._obj.lines[0].set_data((pos[0], pos[0]), (min(*yr) - 1, max(*yr) + 1))
        self._obj.lines[1].set_data((min(*xr) - 1, max(*xr) + 1), (pos[1], pos[1]))

    def _setLineColor(self, color):
        self._obj.lines[0].set_color(color)
        self._obj.lines[1].set_color(color)

    def _setLineStyle(self, style):
        self._obj.lines[0].set_linestyle(style)
        self._obj.lines[1].set_linestyle(style)

    def _setLineWidth(self, width):
        self._obj.lines[0].set_linewidth(width)
        self._obj.lines[1].set_linewidth(width)

    def _setZOrder(self, z):
        _setZ(self._obj.lines[0], z)
        _setZ(self._obj.lines[1], z)

    def _setVisible(self, visible):
        self._obj.lines[0].set_visible(visible)
        self._obj.lines[1].set_visible(visible)

    def remove(self):
        self._obj.lines[0].remove()
        self._obj.lines[1].remove()


class _CrosshairItem(object):
    def __init__(self, canvas, axes, pos):
        self._canvas = canvas
        line1, = axes.plot((pos[0], 0), (pos[0], 0))
        line2, = axes.plot((0, pos[0]), (0, pos[1]))
        self.lines = [line1, line2]
        self.lines[0].set_pickradius(5)
        self.lines[1].set_pickradius(5)


class _MatplotlibTextAnnotation(TextAnnotation):
    def _initialize(self, text, pos, axis):
        self._axes = self.canvas().getAxes(axis)
        self._obj = self._axes.text(pos[0], pos[1], text, transform=self._axes.transAxes, picker=True)

    def _setText(self, txt):
        self._obj.set_text(txt)

    def _setPosition(self, pos):
        self._obj.set_position(pos)

    def _setTransform(self, transformation):
        d = {"axes": self._axes.transAxes, "data": self._axes.transData}
        if isinstance(transformation, str):
            t = d[transformation]
        else:
            t = transforms.blended_transform_factory(d[transformation[0]], d[transformation[1]])
        pos = self.getPosition()
        old = self._obj.get_transform().transform(pos)
        new = t.inverted().transform(old)
        self._obj.set_transform(t)
        self.setPosition(new)

    def _setFont(self, font):
        self._obj.set_family(font.fontName)
        self._obj.set_size(font.size)
        self._obj.set_color(font.color)

    def _setBoxStyle(self, style):
        box = self._obj.get_bbox_patch()
        if style == 'none':
            if box is not None:
                box.set_visible(False)
        else:
            self._obj.set_bbox(dict(boxstyle=style))
            self.setBoxColor(*self.getBoxColor())

    def _setBoxColor(self, faceColor, edgeColor):
        box = self._obj.get_bbox_patch()
        if box is not None:
            box.set_facecolor(faceColor)
            box.set_edgecolor(edgeColor)

    def _setZOrder(self, z):
        _setZ(self._obj, z)

    def _setVisible(self, visible):
        self._obj.set_visible(visible)

    def remove(self):
        self._obj.remove()


class _MatplotlibAnnotation(CanvasAnnotation):
    def _addLineAnnotation(self, *args, **kwargs):
        return _MatplotlibLineAnnotation(self.canvas(), *args, **kwargs)

    def _addInfiniteLineAnnotation(self, *args, **kwargs):
        return _MatplotlibInfiniteLineAnnotation(self.canvas(), *args, **kwargs)

    def _addRectAnnotation(self, *args, **kwargs):
        return _MatplotlibRectAnnotation(self.canvas(), *args, **kwargs)

    def _addRegionAnnotation(self, *args, **kwargs):
        return _MatplotlibRegionAnnotation(self.canvas(), *args, **kwargs)

    def _addFreeRegionAnnotation(self, *args, **kwargs):
        return _MatplotlibFreeRegionAnnotation(self.canvas(), *args, **kwargs)

    def _addCrossAnnotation(self, *args, **kwargs):
        return _MatplotlibCrossAnnotation(self.canvas(), *args, **kwargs)

    def _addTextAnnotation(self, *args, **kwargs):
        return _MatplotlibTextAnnotation(self.canvas(), *args, **kwargs)

    def _removeAnnotation(self, obj):
        obj.remove()
