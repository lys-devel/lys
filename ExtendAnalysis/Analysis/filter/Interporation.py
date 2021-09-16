import numpy as np
from scipy.interpolate import interpn, interp2d, interp1d


from ExtendAnalysis import Wave, DaskWave
from .FilterInterface import FilterInterface


class InterpFilter(FilterInterface):
    def __init__(self, size):
        self._size = size

    def _execute(self, wave, **kwargs):
        sigList1, sigList2 = "a,b,c,d,e,f,g,h", "i,j,k,l,m,n,o,p"
        indice = [i for i in range(len(self._size)) if self._size[i] != 0]
        if len(indice) == 0:
            return
        sig = "(" + sigList1[:len(indice) * 2 - 1] + ")->(" + sigList2[:len(indice) * 2 - 1] + ")"
        newAxes = self.getNewAxes(wave)
        oldAxes = [wave.getAxis(i) for i in indice]
        axes_used = [newAxes[i] for i in indice]
        if len(indice) in [1, 2]:
            def func(x):
                if x.ndim == 2:
                    intp = interp2d(oldAxes[1], oldAxes[0], x, kind="cubic")
                    return intp(axes_used[1], axes_used[0])
                else:
                    intp = interp1d(oldAxes[0], x, kind='quadratic')
                    return intp(axes_used[0])
        else:
            order = list(range(1, len(indice) + 1)) + [0]
            mesh = np.array(np.meshgrid(*axes_used, indexing="ij")).transpose(*order)
            def func(x): return interpn(oldAxes, x, mesh)
        output_sizes = {sigList2[j * 2]: len(newAxes[i]) for j, i in enumerate(indice)}
        uf = self.generalizedFunction(wave, func, sig, [indice, indice], output_sizes=output_sizes)
        wave.data = self._applyFunc(uf, wave.data)
        wave.axes = newAxes
        return wave

    def getNewAxes(self, wave):
        axes = []
        for i in range(len(self._size)):
            ax = wave.getAxis(i)
            if self._size[i] == 0:
                axes.append(ax)
            else:
                axes.append(np.linspace(min(ax), max(ax), self._size[i]))
        return axes
