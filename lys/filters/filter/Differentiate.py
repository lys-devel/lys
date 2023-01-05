import numpy as np
import dask.array as da

from lys import DaskWave
from lys.filters import FilterInterface, FilterSettingBase, filterGUI, addFilter

from .CommonWidgets import AxisCheckLayout


class GradientFilter(FilterInterface):
    """
    Differentiate wave along *axes* (implementation of np.gradient in lys)

    See :class:`.FilterInterface.FilterInterface` for general description of Filters.

    Args:
        axes(list of int): axes to be differentiated

    Example:

        Apply GradientFilter::

            from lys import Wave, filters
            w = Wave([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
            f = filters.GradientFilter(axes=[0])
            result = f.execute(w)
            result.data
            # [1,1,1,1,1]
    """

    def __init__(self, axes):
        self._axes = axes

    def _execute(self, wave, *axes, **kwargs):
        def f(d, x):
            if len(d) == 1:
                return x
            return np.gradient(d, x)
        for ax in self._axes:
            data = da.apply_along_axis(f, ax, wave.data, wave.getAxis(ax))
        return DaskWave(data, *wave.axes, **wave.note)

    def getParameters(self):
        return {"axes": self._axes}


class NablaFilter(FilterInterface):
    """
    Apply nabla vector

    See :class:`.FilterInterface.FilterInterface` for general description of Filters.

    Example:

        Apply NablaFilter::

            import numpy as np
            from lys import Wave, filters
            ar = np.array([1, 2, 3])
            w = Wave([ar + i for i in range(3)], ar, ar, name="wave")
            f = filters.NablaFilter()
            result = f.execute(w)
            print(result.data)
            # [[1,1,1], [1,1,1], [1,1,1]]
    """

    def __init__(self):
        pass

    def _execute(self, wave, *axes, **kwargs):
        def f(d, x):
            if len(d) == 1:
                return x
            return np.gradient(d, x)
        data = da.stack([da.apply_along_axis(f, ax, wave.data, wave.getAxis(ax)) for ax in range(wave.data.ndim)])
        return DaskWave(data, None, *wave.axes, **wave.note)

    def getParameters(self):
        return {}

    def getRelativeDimension(self):
        return 1


class LaplacianFilter(FilterInterface):
    """
    Apply Laplacian

    See :class:`.FilterInterface.FilterInterface` for general description of Filters.

    Example:

        Apply LaplacianFilter::

            import numpy as np
            from lys import Wave, filters
            x = np.linspace(0,100,100)
            w = Wave(x**2, x)
            f = filters.LaplacianFilter()
            result = f.execute(w)
            result.data
            # [1, 1.5, 2, 2, 2, ...]
    """

    def __init__(self):
        pass

    def _execute(self, wave, *axes, **kwargs):
        def f(d, x):
            if len(d) == 1:
                return x
            return np.gradient(np.gradient(d, x), x)
        data = da.stack([da.apply_along_axis(f, ax, wave.data, wave.getAxis(ax)) for ax in range(wave.data.ndim)]).sum(axis=0)
        return DaskWave(data, None, *wave.axes, **wave.note)

    def getParameters(self):
        return {}


class _AxisCheckSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self._layout = AxisCheckLayout(dim)
        self.setLayout(self._layout)

    def setParameters(self, axes):
        self._layout.SetChecked(axes)

    def getParameters(self):
        return {"axes": self._layout.GetChecked()}


@filterGUI(GradientFilter)
class _GradientSetting(_AxisCheckSetting):
    pass


@filterGUI(NablaFilter)
class _NablaSetting(FilterSettingBase):
    def setParameters(self):
        pass

    def getParameters(self):
        return {}


@filterGUI(LaplacianFilter)
class _LaplacianSetting(FilterSettingBase):
    def setParameters(self):
        pass

    def getParameters(self):
        return {}


addFilter(GradientFilter, gui=_GradientSetting, guiName="Gradient", guiGroup="Differentiate")
addFilter(NablaFilter, gui=_NablaSetting, guiName="Nabla vector", guiGroup="Differentiate")
addFilter(LaplacianFilter, gui=_LaplacianSetting, guiName="Laplacian", guiGroup="Differentiate")
