import numpy as np
from scipy import ndimage
import dask.array as da

from lys import DaskWave
from .FilterInterface import FilterInterface


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
            f = filters.FreeLineFilter(axes=[0, 1], range=[(1, 3), (1, 3)], width=1)
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
        return self._execute_dask(wave, self._axes, self._width)

    def _execute_dask(self, wave, axes, width):
        coord = []
        for j in range(1 - width, width, 2):
            x, y, size = self.__makeCoordinates(wave, axes, j)
            coord.append(np.array([x, y]))
        gumap = da.gufunc(map, signature="(i,j),(p,q,r)->(m)", output_dtypes=wave.data.dtype, vectorize=True, axes=[tuple(axes), (0, 1, 2), (min(axes),)], allow_rechunk=True, output_sizes={"m": size})
        res = gumap(wave.data, da.from_array(coord))
        return self.__setAxesAndData(wave, axes, size, res)

    def __makeCoordinates(self, wave, axes, j):
        pos1 = (wave.posToPoint(self.position[0][0], axes[0]), wave.posToPoint(self.position[1][0], axes[1]))
        pos2 = (wave.posToPoint(self.position[0][1], axes[0]), wave.posToPoint(self.position[1][1], axes[1]))
        dx = (pos2[0] - pos1[0])
        dy = (pos2[1] - pos1[1])
        size = int(np.sqrt(dx * dx + dy * dy) + 1)
        nor = np.sqrt(dx * dx + dy * dy)
        dx, dy = dy / nor, -dx / nor
        return np.linspace(pos1[0], pos2[0], size) + dx * (j * 0.5), np.linspace(pos1[1], pos2[1], size) + dy * (j * 0.5), size

    def __setAxesAndData(self, wave, axes, size, res):
        pos1 = (wave.posToPoint(self.position[0][0], axes[0]), wave.posToPoint(self.position[1][0], axes[1]))
        pos2 = (wave.posToPoint(self.position[0][1], axes[0]), wave.posToPoint(self.position[1][1], axes[1]))
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
