import numpy as np
import itertools
from ExtendAnalysis import Wave, DaskWave
from .FilterInterface import FilterInterface


class ReduceSizeFilter(FilterInterface):
    def __init__(self, kernel):
        self.kernel = kernel

    def _execute(self, wave, **kwargs):
        axes = []
        for i, k in enumerate(self.kernel):
            a = wave.axes[i]
            if (a == np.array(None)).all():
                axes.append(a)
            else:
                axes.append(wave.axes[i][0::k])
        res = None
        rans = [range(k) for k in self.kernel]
        for list in itertools.product(*rans):
            sl = tuple([slice(x, None, step) for x, step in zip(list, self.kernel)])
            if res is None:
                res = wave.data[sl]
            else:
                res += wave.data[sl]
        wave.data = res
        wave.axes = axes
        return wave

    def getKernel(self):
        return self.kernel
