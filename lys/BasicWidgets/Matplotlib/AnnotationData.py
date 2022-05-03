from matplotlib import transforms, patches
from ..CanvasInterface import CanvasAnnotation, LineAnnotation, InfiniteLineAnnotation, TextAnnotation, RectAnnotation


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
        self._obj.set_zorder(z)

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
        self._obj.set_zorder(z)

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
        self._obj.set_zorder(z)

    def _setVisible(self, visible):
        self._obj.set_visible(visible)

    def remove(self):
        self._obj.remove()


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

    def _setFont(self, family, size, color):
        self._obj.set_family(family)
        self._obj.set_size(size)
        self._obj.set_color(color)

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
        self._obj.set_zorder(z)

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

    def _addRgionAnnotation(self, *args, **kwargs):
        raise NotImplementedError(str(type(self)) + " does not support region annotation.")

    def _addCrossAnnotation(self, *args, **kwargs):
        raise NotImplementedError(str(type(self)) + " does not support crossannotation.")

    def _addTextAnnotation(self, *args, **kwargs):
        return _MatplotlibTextAnnotation(self.canvas(), *args, **kwargs)

    def _removeAnnotation(self, obj):
        obj.remove()
