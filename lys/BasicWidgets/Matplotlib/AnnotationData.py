from ..CanvasInterface import LineAnnotation


class _MatplotlibLineAnnotation(LineAnnotation):
    def __init__(self, canvas, pos, axis):
        super().__init__(canvas, pos, axis)
        axes = canvas.getAxes(axis)
        self._obj, = axes.plot((pos[0][0], pos[1][0]), (pos[0][1], pos[1][1]), picker=5)

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
