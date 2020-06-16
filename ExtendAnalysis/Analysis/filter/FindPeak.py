import numpy as np

from scipy.signal import *

from ExtendAnalysis import Wave, DaskWave
from .FilterInterface import FilterInterface

import dask.array as da


class PeakFilter(FilterInterface):
    def __init__(self, axis, order, type="ArgRelMax"):
        self._order = order
        self._type = type
        self._axis = axis

    def _execute(self, wave, *args, **kwargs):
        def relmax(x, order):
            res = argrelextrema(x, np.greater_equal, order=order)[0]
            if len(res) == 0:
                return 0
            peak = res[np.argmax([x[i] for i in res])]
            return peak

        def relmin(x, order):
            res = argrelextrema(x, np.less_equal, order=order)[0]
            if len(res) == 0:
                return 0
            peak = res[np.argmin([x[i] for i in res])]
            return peak
        if self._type == "ArgRelMax":
            f = relmax
        else:
            f = relmin
        axes = [ax for ax in wave.axes]
        axes.pop(self._axis)
        if isinstance(wave, Wave):
            uf = np.vectorize(f, signature="(i),()->()")
            tran = list(range(wave.data.ndim))
            tran.remove(self._axis)
            tran.append(self._axis)
            wave.data = uf(wave.data.transpose(*tran), self._order)
        if isinstance(wave, DaskWave):
            uf = da.gufunc(f, signature="(i),()->()", output_dtypes=float, vectorize=True, axes=[(self._axis,), (), ()], allow_rechunk=True)
            wave.data = uf(wave.data, self._order)
        wave.axes = axes
        return wave

    def getParams(self):
        return self._axis, self._order, self._type
