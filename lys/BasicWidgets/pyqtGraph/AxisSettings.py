import warnings
import pyqtgraph as pg

from LysQt.QtGui import QColor

from lys.errors import NotSupportedWarning
from ..CanvasInterface import CanvasAxes, CanvasTicks

_opposite = {'Left': 'right', 'Right': 'left', 'Bottom': 'top', 'Top': 'bottom'}
_Opposite = {'Left': 'Right', 'Right': 'Left', 'Bottom': 'Top', 'Top': 'Bottom', 'left': 'Right', 'right': 'Left', 'bottom': 'Top', 'top': 'Bottom'}


class _pyqtGraphAxes(CanvasAxes):
    """Implementation of CanvasAxes for pyqtgraph"""

    def __init__(self, canvas):
        super().__init__(canvas)
        self.__resizing = False
        self.__initAxes(canvas)
        self.__initROI()

    def __initAxes(self, canvas):
        self._axes = canvas.fig.vb

        self._axes_tx = None
        self._axes_tx_com = pg.ViewBox()
        canvas.fig.scene().addItem(self._axes_tx_com)
        canvas.fig.getAxis('right').linkToView(self._axes_tx_com)
        self._axes_tx_com.setXLink(self._axes)
        self._axes_tx_com.setYLink(self._axes)

        self._axes_ty = None
        self._axes_ty_com = pg.ViewBox()
        canvas.fig.scene().addItem(self._axes_ty_com)
        canvas.fig.getAxis('top').linkToView(self._axes_ty_com)
        self._axes_ty_com.setXLink(self._axes)
        self._axes_ty_com.setYLink(self._axes)

        self._axes_txy = None
        self._axes_txy_com = pg.ViewBox()
        canvas.fig.scene().addItem(self._axes_txy_com)
        self._axes_txy_com.setYLink(self._axes_tx_com)
        self._axes_txy_com.setXLink(self._axes_ty_com)

        canvas.fig.getAxis('top').setStyle(showValues=False)
        canvas.fig.getAxis('right').setStyle(showValues=False)

        self._axes.sigResized.connect(self.__updateViews)
        self._axes.sigRangeChanged.connect(lambda: self.__viewRangeChanged("Left"))
        self._axes.sigRangeChanged.connect(lambda: self.__viewRangeChanged("Bottom"))
        self._axes_txy_com.sigRangeChanged.connect(lambda: self.__viewRangeChanged("Top"))
        self._axes_txy_com.sigRangeChanged.connect(lambda: self.__viewRangeChanged("Right"))

    def __initROI(self):
        pen = pg.mkPen(QColor('#ff0000'))
        self.__roi = pg.RectROI([0, 0], [0, 0], invertible=True, movable=False, resizable=False, pen=pen)
        self.__roi.setZValue(100000)
        self.__roi.hide()
        self.__roiflg = False
        self.getAxes('BottomLeft').addItem(self.__roi)

    def __updateViews(self):
        self.__resizing = True
        self._axes_tx_com.setGeometry(self._axes.sceneBoundingRect())
        self._axes_ty_com.setGeometry(self._axes.sceneBoundingRect())
        self._axes_txy_com.setGeometry(self._axes.sceneBoundingRect())
        #self.axes_tx_com.linkedViewChanged(self.axes, self.axes_tx_com.XAxis)
        #self.axes_ty_com.linkedViewChanged(self.axes, self.axes_ty_com.YAxis)
        #self.axes_txy_com.linkedViewChanged(self.axes, self.axes_txy_com.XAxis)
        #self.axes_txy_com.linkedViewChanged(self.axes, self.axes_txy_com.YAxis)
        self.__resizing = False

    def __viewRangeChanged(self, axis):
        if not self.__resizing:
            if "Left" in axis and self.axisIsValid("Left"):
                _, yrange = self.canvas().getAxes("Left").viewRange()
                if yrange != self.getAxisRange("Left"):
                    self.setAxisRange("Left", yrange)
            if "Right" in axis and self.axisIsValid("Right"):
                _, yrange = self.canvas().getAxes("Right").viewRange()
                if yrange != self.getAxisRange("Right"):
                    self.setAxisRange("Right", yrange)
            if "Bottom" in axis and self.axisIsValid("Bottom"):
                xrange, _ = self.canvas().getAxes("Bottom").viewRange()
                if xrange != self.getAxisRange("Bottom"):
                    self.setAxisRange("Bottom", xrange)
            if "Top" in axis and self.axisIsValid("Top"):
                xrange, _ = self.canvas().getAxes("Top").viewRange()
                if xrange != self.getAxisRange("Top"):
                    self.setAxisRange("Top", xrange)

    def __getAxes(self, axis):
        if axis == "BottomLeft":
            return self._axes
        if axis == "TopLeft":
            return self._axes_ty
        if axis == "BottomRight":
            return self._axes_tx
        if axis == "TopRight":
            return self._axes_txy

    def __enableAxes(self, axis):
        if axis == "TopLeft" and self._axes_ty is None:
            self._axes_ty_com.setXLink(None)
            self._axes_ty = self._axes_ty_com
            self.canvas().fig.getAxis('top').setStyle(showValues=True)
        if axis == "BottomRight" and self._axes_tx is None:
            self._axes_tx_com.setYLink(None)
            self._axes_tx = self._axes_tx_com
            self.canvas().fig.getAxis('right').setStyle(showValues=True)
        if axis == "TopRight" and self._axes_txy is None:
            self._axes_ty_com.setXLink(None)
            self._axes_tx_com.setYLink(None)
            self._axes_txy = self._axes_txy_com
            self.canvas().fig.getAxis('top').setStyle(showValues=True)
            self.canvas().fig.getAxis('right').setStyle(showValues=True)

    def _addAxis(self, axis):
        if axis == "Right":
            self.__enableAxes("BottomRight")
        if axis == 'Top':
            self.__enableAxes("TopLeft")
        if self.axisIsValid("Right") and self.axisIsValid("Top"):
            self.__enableAxes("TopRight")

    def getAxes(self, axis='Left'):
        if axis in ["BottomLeft", "BottomRight", "TopLeft", "TopRight"]:
            return self.__getAxes(axis)
        ax = axis
        if ax in ['Left', 'Bottom']:
            return self._axes
        if ax == 'Top':
            if self._axes_ty is not None:
                return self._axes_ty
            else:
                return self._axes_txy
        if ax == 'Right':
            if self._axes_tx is not None:
                return self._axes_tx
            else:
                return self._axes_txy

    def _setRange(self, axis, range):
        axes = self.canvas().getAxes(axis)
        if axis in ['Left', 'Right']:
            axes.setYRange(*range, padding=0)
            axes.disableAutoRange(axis='y')
            axes.invertY(range[0] > range[1])
        if axis in ['Top', 'Bottom']:
            axes.setXRange(*range, padding=0)
            axes.disableAutoRange(axis='x')
            axes.invertX(range[0] > range[1])
        if axis == 'Top' and self._axes_txy is not None:
            self._axes_txy.invertX(range[0] > range[1])
        if axis == 'Right' and self._axes_txy is not None:
            self._axes_txy.invertY(range[0] > range[1])

    def _setAxisThick(self, axis, thick):
        ax = self._getAxisList(axis)
        for a in ax:
            pen = a.pen()
            pen.setWidth(thick)
            c = pen.color()
            if thick == 0:
                c.setAlphaF(0)
            else:
                c.setAlphaF(1)
            pen.setColor(c)
            a.setPen(pen)

    def _setAxisColor(self, axis, color):
        ax = self._getAxisList(axis)
        for a in ax:
            pen = a.pen()
            if isinstance(color, tuple):
                col = [c * 255 for c in color]
                pen.setColor(QColor(*col))
            else:
                pen.setColor(QColor(color))
            a.setPen(pen)

    def _setMirrorAxis(self, axis, value):
        warnings.warn("pyqtGraph does not support show/hide mirror axes.", NotSupportedWarning)

    def _getAxisList(self, axis):
        res = [self.canvas().fig.axes[axis.lower()]['item']]
        if not self.axisIsValid(_Opposite[axis]):
            res.append(self.canvas().fig.axes[_opposite[axis]]['item'])
        return res

    def _setAxisMode(self, axis, mod):
        if mod == 'log':
            warnings.warn("pyqtGraph does not support log scale.", NotSupportedWarning)

    def _setSelectAnnotation(self, region):
        if self.__roiflg:
            return
        if region[0] == region[1]:
            self.__roi.hide()
        else:
            self.__roi.show()
        self.__roiflg = True
        self.__roi.setPos((min(region[0][0], region[1][0]), min(region[0][1], region[1][1])))
        self.__roi.setSize((max(region[0][0], region[1][0]) - min(region[0][0], region[1][0]), max(region[0][1], region[1][1]) - min(region[0][1], region[1][1])))
        self.__roiflg = False
        self.canvas().update()


class _pyqtGraphTicks(CanvasTicks):
    """Implementation of CanvasTicks for pyqtgraph"""

    def _setTickWidth(self, axis, value, which='major'):
        warnings.warn("pyqtGraph does not support setting width axes. Use axis thick instead.", NotSupportedWarning)

    def __alist(self, axis):
        res = [axis]
        if not self.canvas().axisIsValid(_Opposite[axis]):
            res.append(_Opposite[axis])
        return res

    def __set(self, axis, visible, direction, length):
        dir = {"in": -1, "out": 1, 1: 1, -1: -1, None: 0}
        direction = dir[direction]
        if visible:
            visible = 1
        else:
            visible = 0
        ax = self.canvas().fig.axes[axis.lower()]['item']
        ax.setStyle(tickLength=int(direction * length * visible))

    def _setTickInterval(self, axis, value, which='major'):
        for ax in self.__alist(axis):
            ax = self.canvas().fig.axes[ax.lower()]['item']
            if which == 'major':
                if self.getTickVisible(axis, which='minor'):
                    ax.setTickSpacing(major=value, minor=self.getTickInterval(axis, which="minor", raw=False))
                else:
                    ax.setTickSpacing(major=value, minor=value)
            elif self.getTickVisible(axis, which='minor'):
                ax.setTickSpacing(major=self.getTickInterval(axis, which="major", raw=False), minor=value)

    def _setTickDirection(self, axis, direction):
        self.__set(axis, self.getTickVisible(axis), direction, self.getTickLength(axis))
        if not self.canvas().axisIsValid(_Opposite[axis]):
            self.__set(_Opposite[axis], self.getTickVisible(axis, mirror=True), direction, self.getTickLength(axis))

    def _setTickLength(self, axis, value, which='major'):
        if which == 'minor':
            warnings.warn("pyqtGraph does not support setting tick length of minor axes.", NotSupportedWarning)
            return
        self.__set(axis, self.getTickVisible(axis), self.getTickDirection(axis), int(value))
        if not self.canvas().axisIsValid(_Opposite[axis]):
            self.__set(_Opposite[axis], self.getTickVisible(axis, mirror=True), self.getTickDirection(axis), int(value))

    def _setTickVisible(self, axis, tf, mirror=False, which='both'):
        if which in ['both', 'major']:
            if mirror:
                if not self.canvas().axisIsValid(_Opposite[axis]):
                    self.__set(_Opposite[axis], tf, self.getTickDirection(axis), self.getTickLength(axis))
            else:
                self.__set(axis, tf, self.getTickDirection(axis), self.getTickLength(axis))
        if which in ['both', 'minor']:
            if tf:
                w = "minor"
            else:
                w = "major"
            if mirror:
                if not self.canvas().axisIsValid(_Opposite[axis]):
                    ax = self.canvas().fig.axes[_Opposite[axis].lower()]['item']
                    ax.setTickSpacing(major=self.getTickInterval(axis, which="major", raw=False), minor=self.getTickInterval(axis, which=w, raw=False))
            else:
                ax = self.canvas().fig.axes[axis.lower()]['item']
                ax.setTickSpacing(major=self.getTickInterval(axis, which="major", raw=False), minor=self.getTickInterval(axis, which=w, raw=False))
