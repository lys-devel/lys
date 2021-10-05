import numpy as np
from scipy.interpolate import interpn, interp2d, interp1d

from lys.filters import FilterSettingBase, filterGUI, addFilter

from .FilterInterface import FilterInterface
from .CommonWidgets import QLabel, QSpinBox, QGridLayout


class InterpFilter(FilterInterface):
    """
    Interpolate data by scipy.interpolate

    Args:
        size(tuple of int): new shape

    Example:

        Interpolate quadrutic function::

        import numpy as np
        from lys import Wave, filters
        x = np.linspace(0, 100, 100)
        w = Wave(x**2, x)
        f = filters.InterpFilter(size=(200,))
        result = f.execute(w)
        print(w.shape, result.shape)
        # (100,), (200,)

    """

    def __init__(self, size):
        self._size = size

    def _execute(self, wave, **kwargs):
        sigList1, sigList2 = "a,b,c,d,e,f,g,h", "i,j,k,l,m,n,o,p"
        indice = [i for i in range(len(self._size)) if self._size[i] != 0]
        if len(indice) == 0:
            return
        sig = "(" + sigList1[:len(indice) * 2 - 1] + ")->(" + sigList2[:len(indice) * 2 - 1] + ")"
        newAxes = self._getNewAxes(wave)
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

            def func(x):
                return interpn(oldAxes, x, mesh)
        output_sizes = {sigList2[j * 2]: len(newAxes[i]) for j, i in enumerate(indice)}
        uf = self._generalizedFunction(wave, func, sig, [indice, indice], output_sizes=output_sizes)
        wave.data = self._applyFunc(uf, wave.data)
        wave.axes = newAxes
        return wave

    def _getNewAxes(self, wave):
        axes = []
        for i in range(len(self._size)):
            ax = wave.getAxis(i)
            if self._size[i] == 0:
                axes.append(ax)
            else:
                axes.append(np.linspace(min(ax), max(ax), self._size[i]))
        return axes

    def getParameters(self):
        return {"size": self._size}


@filterGUI(InterpFilter)
class _InterpSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self._vals = []
        self._layout = QGridLayout()
        for d in range(dim):
            self._layout.addWidget(QLabel("Axis" + str(d + 1)), 0, d)
            v = QSpinBox()
            v.setRange(0, 100000)
            self._vals.append(v)
            self._layout.addWidget(v, 1, d)
        self.setLayout(self._layout)

    def getParameters(self):
        return {"size": [v.value() for v in self._vals]}

    def setParameters(self, size):
        for v, s in zip(self._vals, size):
            v.setValue(s)


addFilter(InterpFilter, gui=_InterpSetting, guiName="Interpolation", guiGroup="Resize and interpolation")
