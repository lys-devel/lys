from matplotlib import transforms
from ..CanvasInterface import CanvasAnnotation, LineAnnotation, TextAnnotation


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
    def _addLineAnnotation(self, pos, axis):
        return _MatplotlibLineAnnotation(self.canvas(), pos, axis)

    def _addInfiniteLineAnnotation(self, pos, type, axis):
        raise NotImplementedError(str(type(self)) + " does not support infinite line annotation.")

    def _addRectAnnotation(self, *args, **kwargs):
        raise NotImplementedError(str(type(self)) + " does not support rect annotation.")

    def _addRgionAnnotation(self, *args, **kwargs):
        raise NotImplementedError(str(type(self)) + " does not support region annotation.")

    def _addCrossAnnotation(self, *args, **kwargs):
        raise NotImplementedError(str(type(self)) + " does not support crossannotation.")

    def _addTextAnnotation(self, text, pos, axis):
        return _MatplotlibTextAnnotation(self.canvas(), text, pos, axis)

    def _removeAnnotation(self, obj):
        obj.remove()
