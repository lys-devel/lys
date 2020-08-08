import numpy as np
from scipy.interpolate import interpn

from ExtendAnalysis import Wave, DaskWave
from .FilterInterface import FilterInterface


class InterpFilter(FilterInterface):
    def __init__(self, size):
        self._size = size

    def _execute(self, wave, **kwargs):
        if isinstance(wave, Wave):
            size = self._size
            for i in range(len(size)):
                if size[i] == 0:
                    size[i] = len(wave.getAxis(i))
            axes = [wave.getAxis(i) for i in range(len(self._size))]
            axes_new = [np.linspace(min(ax), max(ax), size[i]) for i, ax in enumerate(axes)]
            order = list(range(1, len(size)+1)) + [0]
            mesh = np.array(np.meshgrid(*axes_new, indexing="ij")).transpose(*order)
            data = interpn(axes, wave.data, mesh)
            wave.data = data
            wave.axes = axes_new
        if isinstance(wave, DaskWave):
            raise NotImplementedError()
        return wave
