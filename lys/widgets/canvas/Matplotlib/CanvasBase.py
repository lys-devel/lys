import io
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from LysQt.QtCore import QMimeData, Qt
from LysQt.QtWidgets import QApplication
from LysQt.QtGui import QImage

from ..interface import CanvasBase, saveCanvas, CanvasContextMenu, CanvasFont, CanvasKeyboardEvent, CanvasFocusEvent, CanvasMouseEvent, CanvasUtilities
from .AxisSettings import _MatplotlibAxes, _MatplotlibTicks
from .AxisLabelSettings import _MatplotlibAxisLabel, _MatplotlibTickLabel
from .AreaSettings import _MatplotlibMargin, _MatplotlibCanvasSize
from .AnnotationData import _MatplotlibAnnotation
from .WaveData import _MatplotlibData


class _MatplotlibMouseEvent(CanvasMouseEvent):
    def __GlobalToAxis(self, x, y, ax):
        loc = self.__GlobalToRatio(x, y, ax)
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        x_ax = xlim[0] + (xlim[1] - xlim[0]) * loc[0]
        y_ax = ylim[0] + (ylim[1] - ylim[0]) * loc[1]
        return (x_ax, y_ax)

    def __GlobalToRatio(self, x, y, ax):
        ran = ax.get_position()
        x_loc = (x - ran.x0 * self.canvas().width()) / ((ran.x1 - ran.x0) * self.canvas().width())
        y_loc = (self.canvas().height() - y - ran.y0 * self.canvas().height()) / ((ran.y1 - ran.y0) * self.canvas().height())
        return [x_loc, y_loc]

    def mapPosition(self, pos, axis):
        ax = self.canvas().getAxes(axis)
        return self.__GlobalToAxis(pos.x(), pos.y(), ax)


class ExtendCanvas(CanvasBase, FigureCanvas):
    def __init__(self, dpi=100):
        CanvasBase.__init__(self)
        FigureCanvas.__init__(self, Figure(dpi=dpi))
        self.setFocusPolicy(Qt.StrongFocus)  # requires to enable key events
        self.updated.connect(self.draw)
        self.__initCanvasParts()
        self.mpl_connect('scroll_event', self._onScroll)

    def __initCanvasParts(self):
        self.addCanvasPart(_MatplotlibData(self))
        self.addCanvasPart(_MatplotlibAxes(self))
        self.addCanvasPart(_MatplotlibTicks(self))
        self.addCanvasPart(CanvasContextMenu(self))
        self.addCanvasPart(CanvasFont(self))
        self.addCanvasPart(_MatplotlibAxisLabel(self))
        self.addCanvasPart(_MatplotlibTickLabel(self))
        self.addCanvasPart(_MatplotlibMargin(self))
        self.addCanvasPart(_MatplotlibCanvasSize(self))
        self.addCanvasPart(_MatplotlibAnnotation(self))
        self.addCanvasPart(CanvasUtilities(self))
        self.addCanvasPart(CanvasKeyboardEvent(self))
        self.addCanvasPart(_MatplotlibMouseEvent(self))
        self.addCanvasPart(CanvasFocusEvent(self))
        self.initCanvas.emit()

    def mouseReleaseEvent(self, event):
        self.mouseReleased.emit(event)
        super().mouseReleaseEvent(event)

    def mousePressEvent(self, event):
        self.mousePressed.emit(event)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        self.mouseMoved.emit(event)
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.keyPressed.emit(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focused.emit(event)

    @saveCanvas
    def _onScroll(self, event):
        region = self.__FindRegion(event.x, event.y)
        if region == "OnGraph":
            axes = self.axisList()
        else:
            axes = [region]
            if region == "Left":
                axes.append("Right")
            if region == "Bottom":
                axes.append("Top")
        for axis in axes:
            self.__ExpandGraph(event.x, event.y, axis, event.step)

    def __ExpandGraph(self, x, y, axis, step):
        if not self.axisIsValid(axis):
            return
        ratio = 1.05**step
        loc = self.__GlobalToRatio(x, y, self.getAxes("BottomLeft"))
        old = self.getAxisRange(axis)
        if self.getAxisMode(axis) == "linear":
            if axis in {"Bottom", "Top"}:
                cent = (old[1] - old[0]) * loc[0] + old[0]
            if axis in {"Left", "Right"}:
                cent = (old[1] - old[0]) * loc[1] + old[0]
            ran = [cent - (cent - old[0]) * ratio, cent + (old[1] - cent) * ratio]
        elif self.getAxisMode(axis) == "log":
            if old[0] > old[1]:
                ran = [old[0] * ratio, old[1] / ratio]
            else:
                ran = [old[0] / ratio, old[1] * ratio]
        self.setAxisRange(axis, ran)

    def __FindRegion(self, x, y):
        ran = self.getAxes("BottomLeft").get_position()
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

    def __GlobalToRatio(self, x, y, ax):
        ran = ax.get_position()
        x_loc = (x - ran.x0 * self.width()) / ((ran.x1 - ran.x0) * self.width())
        y_loc = (y - ran.y0 * self.height()) / ((ran.y1 - ran.y0) * self.height())
        return [x_loc, y_loc]

    def getFigure(self):
        return self.figure

    def finalize(self):
        self.figure.canvas = None


"""

class PicableCanvas(FigureCanvasBase):
    def __init__(self, dpi=100):
        super().__init__(dpi)
        self.mpl_connect('pick_event', self.OnPick)
        self.__pick = False
        self._resetSelection()

    def _resetSelection(self):
        self.selLine = None
        self.selImage = None
        self.selAxis = None
        self.selAnnot = None

    def OnMouseUp(self, event):
        super().OnMouseUp(event)
        self._resetSelection()
        self.__pick = False

    def OnMouseDown(self, event):
        super().OnMouseDown(event)
        if not self.__pick:
            self._resetSelection()
        self.__pick = False

    def OnPick(self, event):
        self.__pick = True
        if isinstance(event.artist, Text):
            self.selAnnot = event.artist
        elif isinstance(event.artist, XAxis) or isinstance(event.artist, YAxis):
            self.selAxis = event.artist
        elif isinstance(event.artist, Line2D):
            if event.artist.get_zorder() < 0:
                self.selLine = event.artist
        elif isinstance(event.artist, AxesImage):
            if event.artist.get_zorder() < 0:
                self.selImage = event.artist

    def getPickedLine(self):
        return self.selLine

    def getPickedImage(self):
        return self.selImage

    def getPickedAxis(self):
        return self.selAxis

    def getPickedAnnotation(self):
        return self.selAnnot

class ExtendCanvas(FigureCanvasBase):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.doubleClicked.connect(self.defModFunc)
        self.modf = weakref.WeakMethod(self.defModFunc)
        self.moveText = False
        self.textPosStart = None
        self.cursorPosStart = None    def OnMouseUp(self, event):
        if self.moveText == True and event.button == 1:
            self.moveText = False
        return super().OnMouseUp(event)


    def OnMouseDown(self, event):
        if event.dblclick:
            self.modf()(self)
            return super().OnMouseDown(event)
            self.annot = self.getPickedAnnotation()
            if self.annot is not None:
                self.modf()(self, 'Annot.')
                self.setSelectedAnnotations(self.annot.get_zorder())
                return super().OnMouseDown(event)
            axis = self.getPickedAxis()
            if axis is not None:
                self.modf()(self, 'Axis')
                # self.setSelectedAxis(self.__findAxis(axis))
                return super().OnMouseDown(event)
            line = self.getPickedLine()
            if line is not None:
                self.modf()(self, 'Lines')
                w = self.getWaveDataFromArtist(line)
                self.setSelectedIndexes(1, w.id)
                return super().OnMouseDown(event)
            image = self.getPickedImage()
            if image is not None:
                self.modf()(self, 'Images')
                w = self.getWaveDataFromArtist(image)
                self.setSelectedIndexes(2, w.id)
                return super().OnMouseDown(event)
        else:
            return super().OnMouseDown(event)
"""
