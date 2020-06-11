import numpy as np
import itertools
from scipy import ndimage
import dask
import dask.array as da

from ExtendAnalysis import *
from .FilterInterface import FilterInterface


class FreeLineFilter(FilterInterface):
    def __init__(self, axes, range, width):
        self._range = range
        self._axes = axes
        self._width = width
        self.position = range

    def _execute(self, wave, **kwargs):
        if isinstance(wave, Wave):
            return self._execute_wave(wave, self._axes, self._width)
        if isinstance(wave, DaskWave):
            return self._execute_dask(wave, self._axes, self._width)

    def _execute_dask(self, wave, axes, width):
        def map(x, coords):
            return np.sum([ndimage.map_coordinates(x, c, order=1) for c in coords], axis=0)
        coord = []
        for j in range(1 - width, width, 2):
            x, y, size = self.__makeCoordinates(wave, axes, j)
            coord.append(np.array([x, y]))
        gumap = da.gufunc(map, signature="(i,j),(p,q,r)->(m)",
                          output_dtypes=wave.data.dtype, vectorize=True, axes=[tuple(axes), (0, 1, 2), (0,)], allow_rechunk=True, output_sizes={"m": size})
        res = gumap(wave.data, da.from_array(coord))
        self.__setAxesAndData(wave, axes, size, res)
        return wave

    def _execute_wave(self, wave, axes, width):
        def map(x, coords):
            return np.sum([ndimage.map_coordinates(x, c, order=1) for c in coords], axis=0)
        coord = []
        for j in range(1 - width, width, 2):
            x, y, size = self.__makeCoordinates(wave, axes, j)
            coord.append(np.array([x, y]))
        newaxes, origaxes = self.__makeNewAxes(wave, axes)
        gumap = np.vectorize(map, signature="(i,j),(p,q,r)->(m)")
        res = gumap(wave.data.transpose(*newaxes), np.array(coord)).transpose(*origaxes)
        self.__setAxesAndData(wave, axes, size, res)
        return wave

    def __makeNewAxes(self, wave, axes):
        newaxes = [*range(wave.data.ndim)]
        for a in axes:
            newaxes.remove(a)
        newaxes.extend(axes)
        origaxes = list(range(wave.data.ndim - 2))
        origaxes.insert(min(axes), wave.data.ndim - 2)
        return newaxes, origaxes

    def __makeCoordinates(self, wave, axes, j):
        pos1 = (wave.posToPoint(self.position[0][0], axes[0]), wave.posToPoint(self.position[1][0], axes[0]))
        pos2 = (wave.posToPoint(self.position[0][1], axes[1]), wave.posToPoint(self.position[1][1], axes[1]))
        dx = (pos2[0] - pos1[0])
        dy = (pos2[1] - pos1[1])
        size = int(np.sqrt(dx * dx + dy * dy) + 1)
        nor = np.sqrt(dx * dx + dy * dy)
        dx, dy = dy / nor, -dx / nor
        return np.linspace(pos1[0], pos2[0], size) + dx * (j * 0.5), np.linspace(pos1[1], pos2[1], size) + dy * (j * 0.5), size

    def __setAxesAndData(self, wave, axes, size, res):
        pos1 = (wave.posToPoint(self.position[0][0], axes[0]), wave.posToPoint(self.position[1][0], axes[0]))
        pos2 = (wave.posToPoint(self.position[0][1], axes[1]), wave.posToPoint(self.position[1][1], axes[1]))
        replacedAxis = min(*axes)
        if wave.axisIsValid(axes[0]):
            axis1 = wave.axes[axes[0]]
        else:
            axis1 = list(range(wave.data.shape[axes[0]]))
        if wave.axisIsValid(axes[1]):
            axis2 = wave.axes[axes[1]]
        else:
            axis2 = list(range(wave.data.shape[axes[1]]))
        dx = abs(axis1[pos1[0]] - axis1[pos2[0]])
        dy = abs(axis2[pos1[1]] - axis2[pos2[1]])
        d = np.sqrt(dx * dx + dy * dy)
        axisData = np.linspace(0, d, size)
        wave.axes[replacedAxis] = axisData
        wave.axes = list(np.delete(wave.axes, max(*axes), 0))
        wave.data = res

    def getParams(self):
        return self._axes, self._range, self._width
