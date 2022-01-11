from matplotlib import ticker, patches

from ..CanvasInterface import CanvasAxes, CanvasTicks

_opposite = {'Left': 'right', 'Right': 'left', 'Bottom': 'top', 'Top': 'bottom'}
_Opposite = {'Left': 'Right', 'Right': 'Left', 'Bottom': 'Top', 'Top': 'Bottom'}


class _MatplotlibAxes(CanvasAxes):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.__initAxes(canvas)
        self.__rect = patches.Rectangle((0, 0), 0, 0, color='orange', alpha=0.5)
        patch = self._axes.add_patch(self.__rect)
        patch.set_zorder(20000)

    def __initAxes(self, canvas):
        self._axes = canvas.fig.add_subplot(111)  # TODO #This line takes 0.3s for each image.
        self._axes.minorticks_on()
        self._axes.xaxis.set_picker(15)
        self._axes.yaxis.set_picker(15)
        self._axes_tx = None
        self._axes_ty = None
        self._axes_txy = None

    def __getAxes(self, axis):
        if axis == "BottomLeft":
            return self._axes
        if axis == "TopLeft":
            return self._axes_ty
        if axis == "BottomRight":
            return self._axes_tx
        if axis == "TopRight":
            return self._axes_txy

    def getAxes(self, axis='Left'):
        if axis in ['BottomLeft', 'BottomRight', 'TopLeft', 'TopRight']:
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

    def _addAxis(self, axis):
        if axis == "Right":
            self.__enableAxes("BottomRight")
        if axis == 'Top':
            self.__enableAxes("TopLeft")
        if self.axisIsValid("Right") and self.axisIsValid("Top"):
            self.__enableAxes("TopRight")

    def __enableAxes(self, axis):
        if axis == "TopLeft" and self._axes_ty is None:
            self._axes_ty = self._axes.twiny()
            self._axes_ty.spines['left'].set_visible(False)
            self._axes_ty.spines['right'].set_visible(False)
            self._axes_ty.xaxis.set_picker(15)
            self._axes_ty.yaxis.set_picker(15)
            self._axes_ty.minorticks_on()
        if axis == 'BottomRight' and self._axes_tx is None:
            self._axes_tx = self._axes.twinx()
            self._axes_tx.spines['top'].set_visible(False)
            self._axes_tx.spines['bottom'].set_visible(False)
            self._axes_tx.xaxis.set_picker(15)
            self._axes_tx.yaxis.set_picker(15)
            self._axes_tx.minorticks_on()
        if axis == "TopRight" and self._axes_txy is None:
            self._axes_txy = self._axes_tx.twiny()
            self._axes_txy.get_xaxis().set_tick_params(top=False, labeltop=False, which="both")
            self._axes_txy.xaxis.set_picker(15)
            self._axes_txy.yaxis.set_picker(15)

    def _setRange(self, axis, range):
        axes = self.getAxes(axis)
        if axis in ['Left', 'Right']:
            axes.set_ylim(range)
        if axis in ['Top', 'Bottom']:
            axes.set_xlim(range)
        if axis == 'Top':
            topAxes = self.getAxes("TopRight")
            if topAxes is not None:
                topAxes.set_xlim(range)

    def _setAxisThick(self, axis, thick):
        axes = self.getAxes(axis)
        axes.spines[axis.lower()].set_linewidth(thick)
        axes.spines[_opposite[axis]].set_linewidth(thick)

    def _setAxisColor(self, axis, color):
        axes = self.getAxes(axis)
        axes.spines[axis.lower()].set_edgecolor(color)
        axes.spines[_opposite[axis]].set_edgecolor(color)
        if axis in ['Left', 'Right']:
            axes.get_yaxis().set_tick_params(color=color, which='both')
        if axis in ['Top', 'Bottom']:
            axes.get_xaxis().set_tick_params(color=color, which='both')

    def _setMirrorAxis(self, axis, value):
        self.getAxes(axis).spines[_opposite[axis]].set_visible(value)

    def _setAxisMode(self, axis, mod):
        axes = self.getAxes(axis)
        if axis in ['Left', 'Right']:
            axes.set_yscale(mod)
        else:
            axes.set_xscale(mod)

    def _setSelectAnnotation(self, region):
        self.__rect.set_xy((min(region[0][0], region[1][0]), min(region[0][1], region[1][1])))
        self.__rect.set_width(max(region[0][0], region[1][0]) - min(region[0][0], region[1][0]))
        self.__rect.set_height(max(region[0][1], region[1][1]) - min(region[0][1], region[1][1]))
        self.canvas().draw()


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
        if self.canvas().getAxisMode(axis) == 'linear':
            loc = ticker.MultipleLocator(interval)
        else:
            print("log", 10**interval, which)
            loc = ticker.LogLocator(base=10**interval)
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
