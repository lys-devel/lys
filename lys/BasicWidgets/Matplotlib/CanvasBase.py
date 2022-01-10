from ..CanvasInterface import CanvasBase, CanvasContextMenu, CanvasFont
from ..CanvasInterface import *
from lys import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .AxisSettings import _MatplotlibAxes, _MatplotlibTicks
from .AxisLabelSettings import _MatplotlibAxisLabel, _MatplotlibTickLabel
from .AreaSettings import _MatplotlibMargin, _MatplotlibCanvasSize
from .AnnotationData import _MatplotlibAnnotation
from .WaveData import _MatplotlibData


class FigureCanvasBase(CanvasBase, FigureCanvas):
    def __init__(self, dpi=100):
        self.fig = Figure(dpi=dpi)
        CanvasBase.__init__(self)
        FigureCanvas.__init__(self, self.fig)
        self.updated.connect(self.draw)
        self.mpl_connect('button_press_event', self.OnMouseDown)
        self.mpl_connect('button_release_event', self.OnMouseUp)
        self.mpl_connect('motion_notify_event', self.OnMouseMove)
        self.mpl_connect('scroll_event', self._onScroll)
        self.__select_rect = False
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

    def getWaveDataFromArtist(self, artist):
        for i in self._Datalist:
            if i.id == artist.get_zorder():
                return i

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
            self.__start = self.__GlobalToAxis(event.x, event.y, self.getAxes("BottomLeft"))
            self.setSelectedRange([self.__start, self.__start])
            self.__select_rect = True

    def OnMouseMove(self, event):
        if self.__select_rect:
            end = self.__GlobalToAxis(event.x, event.y, self.getAxes("BottomLeft"))
            self.setSelectedRange([self.__start, end])

    def OnMouseUp(self, event):
        if self.__select_rect and event.button == 1:
            self.__select_rect = False

    @saveCanvas
    def _onScroll(self, event):
        region = self.__FindRegion(event.x, event.y)
        if region == "OnGraph":
            self.__ExpandGraph(event.x, event.y, "Bottom", event.step)
            self.__ExpandGraph(event.x, event.y, "Left", event.step)
        elif not region == "OutOfFigure":
            self.__ExpandGraph(event.x, event.y, region, event.step)

    def __ExpandGraph(self, x, y, axis, step):
        ratio = 1.05**step
        loc = self.__GlobalToRatio(x, y, self.getAxes("BottomLeft"))
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

    def SaveFigure(self, path, format):
        self.fig.savefig(path, transparent=True, format=format)

    def CopyToClipboard(self):
        clipboard = QApplication.clipboard()
        mime = QMimeData()
        mime.setData('Encapsulated PostScript', self.__toData('eps'))
        mime.setData('application/postscript', self.__toData('eps'))
        mime.setData('Scalable Vector Graphics', self.__toData('svg'))
        mime.setData('application/svg+xml', self.__toData('svg'))
        mime.setData('Portable Document Format', self.__toData('pdf'))
        mime.setData('application/pdf', self.__toData('pdf'))
        try:
            mime.setText(self.__toData('pdf').hex())
        except:
            import traceback
            print(traceback.format_exc())
        buf = io.BytesIO()
        self.fig.savefig(buf, transparent=True)
        mime.setImageData(QImage.fromData(buf.getvalue()))
        buf.close()
        clipboard.setMimeData(mime)

    def __toData(self, format):
        buf = io.BytesIO()
        self.fig.savefig(buf, format=format, transparent=True)
        buf.seek(0)
        data = buf.read()
        buf.close()
        return data

    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        if e.modifiers() == Qt.ControlModifier:
            if e.key() == Qt.Key_C:
                self.CopyToClipboard()


"""
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

"""
