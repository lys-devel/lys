import numpy as np
from scipy import ndimage
import dask.array as da


from lys import DaskWave, frontCanvas
from lys.filters import FilterInterface, FilterSettingBase, filterGUI, addFilter

from lys.Qt import QtWidgets
from lys.widgets import ScientificSpinBox

from .CommonWidgets import AxisSelectionLayout, AxesSelectionDialog


class FreeLineFilter(FilterInterface):
    """
    Cut 2-dimensional data along arbitrary line with finite width.

    *range* specifies start and end points in axes coordinates, [(x1, y1), (x2, y2)].
    For example, [(0,0),(5,10)] means that data is cut along y=2x.

    Args:
        axes(tuple of size 2): axes to be cut.
        range(2*2 sequence): see description above.
        width(int): width of integration around the line in pixel unit.

    Example:

        Cut along line::

            w = Wave([[1, 2, 3], [2, 3, 4], [3, 4, 5]], [1, 2, 3], [1, 2, 3], name="wave")
            f = filters.FreeLineFilter(axes=[0, 1], range=[(1, 1), (3, 3)], width=1)
            result = f.execute(w)
            print(result.data)
            # [1, 3, 5]
    """

    def __init__(self, axes, range, width):
        self._range = range
        self._axes = axes
        self._width = width
        self.position = range

    def _execute(self, wave, *axes, **kwargs):
        width = self.__calcWidthInPixel(wave, self._axes, self._width)
        return self._execute_dask(wave, self._axes, width)

    def __calcWidthInPixel(self, wave, axes, width):
        ax = wave.getAxis(axes[0])
        dx = (ax[-1] - ax[0]) / (len(ax) - 1)
        return max(1, int(np.round(width / dx)))

    def _execute_dask(self, wave, axes, width):
        coord = []
        for j in range(1 - width, width, 2):
            x, y, size = self.__makeCoordinates(wave, axes, j)
            coord.append(np.array([x, y]))
        gumap = da.gufunc(map, signature="(i,j),(p,q,r)->(m)", output_dtypes=wave.data.dtype, vectorize=True, axes=[tuple(axes), (0, 1, 2), (min(axes),)], allow_rechunk=True, output_sizes={"m": size})
        res = gumap(wave.data, da.from_array(coord))
        return self.__setAxesAndData(wave, axes, size, res)

    def __makeCoordinates(self, wave, axes, j):
        pos1 = (wave.posToPoint(self.position[0][0], axes[0]), wave.posToPoint(self.position[0][1], axes[1]))
        pos2 = (wave.posToPoint(self.position[1][0], axes[0]), wave.posToPoint(self.position[1][1], axes[1]))
        dx = (pos2[0] - pos1[0])
        dy = (pos2[1] - pos1[1])
        size = int(np.sqrt(dx * dx + dy * dy) + 1)
        nor = np.sqrt(dx * dx + dy * dy)
        dx, dy = dy / nor, -dx / nor
        return np.linspace(pos1[0], pos2[0], size) + dx * (j * 0.5), np.linspace(pos1[1], pos2[1], size) + dy * (j * 0.5), size

    def __setAxesAndData(self, wave, axes, size, res):
        pos1 = (wave.posToPoint(self.position[0][0], axes[0]), wave.posToPoint(self.position[0][1], axes[1]))
        pos2 = (wave.posToPoint(self.position[1][0], axes[0]), wave.posToPoint(self.position[1][1], axes[1]))
        axis1 = wave.getAxis(axes[0])
        axis2 = wave.getAxis(axes[1])
        dx = abs(axis1[pos1[0]] - axis1[pos2[0]])
        dy = abs(axis2[pos1[1]] - axis2[pos2[1]])
        d = np.sqrt(dx * dx + dy * dy)
        axisData = np.linspace(0, d, size)
        newAxes = list(wave.axes)
        newAxes[min(*axes)] = axisData
        newAxes.pop(max(*axes))
        return DaskWave(res, *newAxes, **wave.note)

    def getParameters(self):
        return {"axes": self._axes, "range": self._range, "width": self._width}

    def getRelativeDimension(self):
        return -1


def map(x, coords):
    if x.dtype == complex:
        real = np.sum([ndimage.map_coordinates(np.real(x), c, order=1) for c in coords], axis=0)
        imag = np.sum([ndimage.map_coordinates(np.imag(x), c, order=1) for c in coords], axis=0)
        return real + imag * 1j
    else:
        return np.sum([ndimage.map_coordinates(x, c, order=1) for c in coords], axis=0)


@filterGUI(FreeLineFilter)
class _FreeLineSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self.__initlayout()

    def __initlayout(self):
        self.width = QtWidgets.QSpinBox()
        self.width.setValue(3)
        self.load = QtWidgets.QPushButton("Load from Graph", clicked=self.__load)

        h3 = QtWidgets.QHBoxLayout()
        h3.addWidget(QtWidgets.QLabel("Width"))
        h3.addWidget(self.width)
        h3.addWidget(self.load)

        self.axis1 = AxisSelectionLayout("Axis 1", self.dim, 0)
        self.from1 = ScientificSpinBox()
        self.from2 = ScientificSpinBox()

        self.axis2 = AxisSelectionLayout("Axis 2", self.dim, 1)
        self.to1 = ScientificSpinBox()
        self.to2 = ScientificSpinBox()

        h1 = QtWidgets.QHBoxLayout()
        h1.addLayout(self.axis1)
        h1.addWidget(self.from1)
        h1.addWidget(self.to1)

        h2 = QtWidgets.QHBoxLayout()
        h2.addLayout(self.axis2)
        h2.addWidget(self.from2)
        h2.addWidget(self.to2)

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.addLayout(h3)
        self._layout.addLayout(h1)
        self._layout.addLayout(h2)
        self.setLayout(self._layout)

    def __load(self):
        c = frontCanvas()
        if c is None:
            return
        lines = c.getLineAnnotations()
        if len(lines) == 0:
            return
        if self.dim != 2:
            d = AxesSelectionDialog(self.dim)
            value = d.exec_()
            if value:
                ax = d.getAxes()
                self.axis1.setAxis(ax[0])
                self.axis2.setAxis(ax[1])
            else:
                return
        line = lines[0]
        p = np.array(line.getPosition()).T
        self.from1.setValue(p[0][0])
        self.to1.setValue(p[0][1])
        self.from2.setValue(p[1][0])
        self.to2.setValue(p[1][1])

    def getParameters(self):
        axes = [self.axis1.getAxis(), self.axis2.getAxis()]
        range = [[self.from1.value(), self.to1.value()], [self.from2.value(), self.to2.value()]]
        width = self.width.value()
        return {"axes": axes, "range": range, "width": width}

    def setParameters(self, axes, range, width):
        self.axis1.setAxis(axes[0])
        self.axis2.setAxis(axes[1])
        self.from1.setValue(range[0][0])
        self.to1.setValue(range[0][1])
        self.from2.setValue(range[1][0])
        self.to2.setValue(range[1][1])
        self.width.setValue(width)


addFilter(FreeLineFilter, gui=_FreeLineSetting, guiName="Cut along line")
