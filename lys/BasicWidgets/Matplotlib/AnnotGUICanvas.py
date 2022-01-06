from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from lys import *

from .Annotation import *


class AnnotGUICanvas(AnnotationSettingCanvas, AnnotGUICanvasBase):
    def __init__(self, dpi):
        super().__init__(dpi)
        AnnotGUICanvasBase.__init__(self)
        self.__drawflg = False

    def constructContextMenu(self):
        menu = super().constructContextMenu()
        return AnnotGUICanvasBase.constructContextMenu(self, menu)

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
        if self._getMode() == "line":
            if event.button == 1:
                self.__drawflg = True
                #self.__saved = self.copy_from_bbox(self.axes.bbox)
                ax = self.__GlobalToAxis(event.x, event.y, self.axes)
                self._pos_start = ax
                self.__line, = self.axes.plot([ax[0]], [ax[1]])
        else:
            return super().OnMouseDown(event)

    def OnMouseUp(self, event):
        if self._getMode() == "line":
            if self.__drawflg == True and event.button == 1:
                ax = self.__GlobalToAxis(event.x, event.y, self.axes)
                if not self._pos_start == ax:
                    self.addLine((self._pos_start, ax))
                self.__line.set_data([], [])
                self.draw()
                self.__drawflg = False
        else:
            return super().OnMouseUp(event)

    def OnMouseMove(self, event):
        if self._getMode() == "line":
            if self.__drawflg == True:
                ax = self.__GlobalToAxis(event.x, event.y, self.axes)
                self.__line.set_data([self._pos_start[0], ax[0]], [self._pos_start[1], ax[1]])
                self.draw()
        else:
            return super().OnMouseMove(event)
