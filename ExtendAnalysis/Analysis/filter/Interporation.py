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
                    size[i] = len(wave.axes[i])
            axes_new = [np.linspace(min(wave.axes[i]), max(wave.axes[i]), size[i]) for i in range(len(self._size))]
            data = interpn(wave.axes, wave.data, np.array(np.meshgrid(*axes_new)).T)
            wave.axes = axes_new
            wave.data = data
        if isinstance(wave, DaskWave):
            raise NotImplementedError()
        return wave
