import numpy as np
import dask.array as da

from lys import DaskWave
from lys.Qt import QtWidgets
from lys.filters import FilterInterface, FilterSettingBase, filterGUI, addFilter
from lys.widgets import AxisCheckLayout, AxisSelectionLayout


class GradientFilter(FilterInterface):
    """
    Differentiate wave along *axes* (implementation of np.gradient in lys)

    Args:
        axes(list of int): axes to be differentiated

    Example::

        from lys import Wave, filters

        w = Wave([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])

        f = filters.GradientFilter(axes=[0])
        result = f.execute(w)
        print(result.data) # [1,1,1,1,1]

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

    Args:
        axes(list of int): axes to be differentiated. If None, all axes will be differentiated.

    Example::

        import numpy as np
        from lys import Wave, filters

        ar = np.array([1, 2, 3])
        w = Wave([ar + i for i in range(3)], ar, ar, name="wave")

        f = filters.NablaFilter()
        result = f.execute(w)
        print(result.data) # [[1,1,1], [1,1,1], [1,1,1]]
    """
    def __init__(self, axes=None):
        self._axes = axes

    def _execute(self, wave, *axes, **kwargs):
        data = da.gradient(wave.data, axis = self._axes)[::-1]
        return DaskWave(data, None, *wave.axes, **wave.note)

    def getParameters(self):
        return {"axes": self._axes}

    def getRelativeDimension(self):
        return 1
    

class CurlFilter(FilterInterface):
    """
    Apply curl to vector function f(x,y,z)

    Args:
        axis_vector(int): Axis of vector. The input wave should be a size 2 or 3 vector along this dimension.
        axes_xyz(tuple of int): axes of coordinates x,y,z. If one of the axes is None, f(x,y,z) is assumed to be independent of the axis.
    """

    def __init__(self, axis_vector=0, axes_xyz=(1,2,3)):
        self._axis_vector = axis_vector
        self._axes_xyz = axes_xyz

    def _execute(self, wave, *args, **kwargs):
        dx, dy, dz = [da.gradient(wave.data, axis = ax) if ax is not None else wave.data*0 for ax in self._axes_xyz]
        indices = list(range(wave.shape[self._axis_vector]))
        dv_dx = da.take(dx, indices, axis=self._axis_vector)
        dv_dy = da.take(dy, indices, axis=self._axis_vector)
        dv_dz = da.take(dz, indices, axis=self._axis_vector)
        if len(indices) == 3:
            data = da.stack([dv_dy[2] - dv_dz[1], dv_dz[0] - dv_dx[2], dv_dx[1] - dv_dy[0]])
        elif len(indices) == 2:
            data = da.stack([-dv_dz[1], dv_dz[0], dv_dx[1] - dv_dy[0]])
        axes = [None] + wave.axes[:self._axis_vector] + wave.axes[self._axis_vector+1:]
        return DaskWave(data, *axes, **wave.note)
    
    def getParameters(self):
        return {"axis_vector": self._axis_vector, "axes_xyz": self._axes_xyz}
    
    def getRelativeDimension(self):
        return 0


class DivergenceFilter(FilterInterface):
    """
    Apply divergence to vector function f(x,y,z)

    Args:
        axis_vector(int): Axis of vector. The input wave should be a size 2 or 3 vector along this dimension.
        axes_xyz(tuple of int): axes of coordinates x,y,z. If one of the axes is None, f(x,y,z) is assumed to be independent of the axis.
    """

    def __init__(self, axis_vector=0, axes_xyz=(1,2,3)):
        self._axis_vector = axis_vector
        self._axes_xyz = axes_xyz

    def _execute(self, wave, *args, **kwargs):
        dx, dy, dz = [da.gradient(wave.data, axis = ax) if ax is not None else wave.data*0 for ax in self._axes_xyz]
        indices = list(range(wave.shape[self._axis_vector]))
        dv_dx = da.take(dx, indices, axis=self._axis_vector)
        dv_dy = da.take(dy, indices, axis=self._axis_vector)
        dv_dz = da.take(dz, indices, axis=self._axis_vector)
        if len(indices) == 3:
            data = dv_dx[0] + dv_dy[1] + dv_dz[2]
        elif len(indices) == 2:
            data = dv_dx[0] + dv_dy[1]
        axes = wave.axes[:self._axis_vector] + wave.axes[self._axis_vector+1:]
        return DaskWave(data, *axes, **wave.note)
    
    def getParameters(self):
        return {"axis_vector": self._axis_vector, "axes_xyz": self._axes_xyz}
    
    def getRelativeDimension(self):
        return -1

class LaplacianFilter(FilterInterface):
    """
    Apply Laplacian

    See :class:`.FilterInterface.FilterInterface` for general description of Filters.

    Example::

        import numpy as np
        from lys import Wave, filters

        x = np.linspace(0,100,100)
        w = Wave(x**2, x)

        f = filters.LaplacianFilter()
        result = f.execute(w)
        print(result.data) # [1, 1.5, 2, 2, 2, ...]
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
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self._dim = dimension
        self._axes = AxisCheckLayout(dimension)

    def setParameters(self, axes=None):
        if axes is None:
            axes = list(range(self._dim))
        self._axes.SetChecked(axes)

    def getParameters(self):
        return {"axes": self._axes.GetChecked()}


@filterGUI(LaplacianFilter)
class _LaplacianSetting(FilterSettingBase):
    def setParameters(self):
        pass

    def getParameters(self):
        return {}


@filterGUI(CurlFilter)
class _CurlSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self.__initLayout(dimension)

    def __initLayout(self, dimension):
        self._axis = AxisSelectionLayout("Vector axis", dimension)
        self._xyz = [AxisSelectionLayout(name+" axis", dimension, init=-1, acceptNone=True) for name in ("x", "y", "z")]

        lay = QtWidgets.QVBoxLayout()
        lay.addLayout(self._axis)
        lay.addLayout(self._xyz[0])
        lay.addLayout(self._xyz[1])
        lay.addLayout(self._xyz[2])
        self.setLayout(lay)

    def setParameters(self, axis_vector, axes_xyz):
        self._axis.setAxis(axis_vector)
        for i in range(3):
            self._xyz[i].setAxis(axes_xyz[i] if axes_xyz[i] is not None else -1)

    def getParameters(self):
        return {"axis_vector": self._axis.getAxis(), "axes_xyz": [l.getAxis() if l.getAxis() != -1 else None for l in self._xyz]}



@filterGUI(DivergenceFilter)
class _DivergenceSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)
        self.__initLayout(dimension)

    def __initLayout(self, dimension):
        self._axis = AxisSelectionLayout("Vector axis", dimension)
        self._xyz = [AxisSelectionLayout(name+" axis", dimension, init=-1, acceptNone=True) for name in ("x", "y", "z")]

        lay = QtWidgets.QVBoxLayout()
        lay.addLayout(self._axis)
        lay.addLayout(self._xyz[0])
        lay.addLayout(self._xyz[1])
        lay.addLayout(self._xyz[2])
        self.setLayout(lay)

    def setParameters(self, axis_vector, axes_xyz):
        self._axis.setAxis(axis_vector)
        for i in range(3):
            self._xyz[i].setAxis(axes_xyz[i] if axes_xyz[i] is not None else -1)

    def getParameters(self):
        return {"axis_vector": self._axis.getAxis(), "axes_xyz": [l.getAxis() if l.getAxis() != -1 else None for l in self._xyz]}


addFilter(GradientFilter, gui=_GradientSetting, guiName="Gradient", guiGroup="Differentiate")
addFilter(NablaFilter, gui=_NablaSetting, guiName="Nabla vector", guiGroup="Differentiate")
addFilter(DivergenceFilter, gui=_DivergenceSetting, guiName="Divergence", guiGroup="Differentiate")
addFilter(CurlFilter, gui=_CurlSetting, guiName="Curl", guiGroup="Differentiate")
addFilter(LaplacianFilter, gui=_LaplacianSetting, guiName="Laplacian", guiGroup="Differentiate")
