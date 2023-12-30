import weakref
import numpy as np
import pyvista as pv
from lys.Qt import QtGui

from ..interface import CanvasData3D, VolumeData, SurfaceData, LineData, PointData

_key_list = {"triangle": pv.CellType.TRIANGLE, "tetra": pv.CellType.TETRA, "hexa": pv.CellType.HEXAHEDRON, "quad": pv.CellType.QUAD, "pyramid": pv.CellType.PYRAMID, "prism": pv.CellType.WEDGE}
_num_list = {"line": 2, "triangle": 3, "tetra": 4, "hexa": 8, "quad": 4, "pyramid": 5, "prism": 6}


class _pyvistaMeshObject:
    def __init__(self, parent, scalar, mesh, edges):
        self._parent = weakref.ref(parent)
        self._scalar = scalar
        self._mesh = mesh
        self._edges = edges

        self._obj = parent.canvas().plotter.add_mesh(self._mesh, scalars=self._scalar, cmap="viridis")
        if self._edges.n_lines > 0:
            self._obje = parent.canvas().plotter.add_mesh(self._edges, color='k', line_width=3)
        else:
            self._obje = None
        self._type = "scalars"
    
    @property
    def parent(self):
        return self._parent()

    def remove(self):
        self.parent.canvas().plotter.remove_actor(self._obj)
        if self._obje is not None:
            self.parent.canvas().plotter.remove_actor(self._obje)

    def setVisible(self, visible):
        self._obj.visibility = visible
        if self._obje is not None:
            if self.parent.edgesVisible():
                self._obje.visibility = visible
            else:
                self._obje.visibility = False

    def setColor(self, color, type):
        if type == "color":
            c = QtGui.QColor(color)
            c = [c.redF(), c.greenF(), c.blueF()]
            if self._type == "scalars":
                self.__updateMesh(color=c)
            else:
                self._obj.GetProperty().SetColor(c)
            self._type = "color"
        if type == "scalars":
            self.__updateMesh(scalars = self._scalar, cmap = color)
            self._type = "scalars"

    def __updateMesh(self, scalars=None, cmap=None, color=None):
        self.parent.canvas().plotter.remove_actor(self._obj)
        kwargs = {}
        if scalars is not None:
            kwargs["scalars"] = scalars
        if cmap is not None:
            kwargs["cmap"] = cmap
        if color is not None:
            kwargs["color"] = color
        kwargs["show_edges"] = self.parent.meshesVisible()
        self._obj = self.parent.canvas().plotter.add_mesh(self._mesh, **kwargs)
        if not self.parent.getVisible():
            self._obj.visibility = False

    def showMeshes(self, b):
        self._obj.GetProperty().show_edges = b

    def showEdges(self, b):
        if self._obje is not None:
            if self.parent.getVisible():
                self._obje.visibility = b


class _pyvistaVolume(VolumeData):
    """Implementation of VolumeData for pyvista"""

    def __init__(self, canvas, wave):
        super().__init__(canvas, wave)
        self._wave = wave
        self._obj = None
        self._updateData()

    def rayTrace(self, start, end):
        return self._mesh.extract_surface().ray_trace(start, end, first_point=True)[0]

    def _updateData(self):
        if self._obj is not None:
            self._obj.remove()
        self._mesh = pv.UnstructuredGrid({_key_list[key]: np.array(item) for key, item in self._wave.note["elements"].items()}, self._wave.x.astype(float))
        edges = self._mesh.extract_feature_edges(boundary_edges=True)
        self._obj = _pyvistaMeshObject(self, self._wave.data, self._mesh, edges)

    def remove(self):
        self._obj.remove()

    def _setVisible(self, visible):
        self._obj.setVisible(visible)

    def _setColor(self, color, type):
        self._obj.setColor(color, type)

    def _showMeshes(self, b):
        self._obj.showMeshes(b)

    def _showEdges(self, b):
        self._obj.showEdges(b)


class _pyvistaSurface(SurfaceData):
    """Implementation of LineData for pyvista"""

    def __init__(self, canvas, wave):
        super().__init__(canvas, wave)
        self._wave = wave
        self._obj = None
        self._updateData()

    def rayTrace(self, start, end):
        return self._mesh.ray_trace(start, end, first_point=True)[0]

    def _updateData(self):
        if self._obj is not None:
            self._obj.remove()
        faces = [np.ravel(np.hstack([np.ones((len(faces), 1), dtype=int) * _num_list[key], faces])) for key, faces in self._wave.note["elements"].items()]
        self._mesh = pv.PolyData(self._wave.x.astype(float), np.hstack(faces))
        edges = self._mesh.extract_feature_edges(boundary_edges=True)
        self._obj = _pyvistaMeshObject(self, self._wave.data, self._mesh, edges)

    def remove(self):
        self._obj.remove()

    def _setVisible(self, visible):
        self._obj.setVisible(visible)

    def _setColor(self, color, type):
        self._obj.setColor(color, type)

    def _showMeshes(self, b):
        self._obj.showMeshes(b)

    def _showEdges(self, b):
        self._obj.showEdges(b)


class _pyvistaLine(LineData):
    """Implementation of LineData for pyvista"""

    def __init__(self, canvas, wave):
        super().__init__(canvas, wave)
        self._wave = wave
        self._obj = None
        self._updateData()

        self._type = "scalars"

    def _updateData(self):
        wave = self._wave
        canvas = self.canvas()

        if self._obj is not None:
            self.remove()

        self._p0 = np.array([wave.x[i] for i, _ in list(wave.note["elements"].values())[0]])
        self._p1 = np.array([wave.x[i] for _, i in list(wave.note["elements"].values())[0]])
        lines = [np.ravel(np.hstack([np.ones((len(faces), 1), dtype=int) * _num_list[key], faces])) for key, faces in wave.note["elements"].items()]
        self._mesh = pv.PolyData(wave.x.astype(float), lines=np.hstack(lines))
        value, counts = np.unique(wave.note["elements"]["line"], return_counts=True)

        self._obj = canvas.plotter.add_mesh(self._mesh, line_width=4, scalars=wave.data)
        if len(wave.x[value[counts == 1]]) > 0:
            self._obje = canvas.plotter.add_points(wave.x[value[counts == 1]].astype(float), render_points_as_spheres=True, point_size=7, color="k")
        else:
            self._obje = None
        self._mesh_points = self.canvas().plotter.add_points(self._wave.x.astype(float), render_points_as_spheres=True, point_size=5, color="k")
        self._mesh_points.visibility = False
    
    def remove(self):
        self.canvas().plotter.remove_actor(self._obj)
        if self._obje is not None:
            self.canvas().plotter.remove_actor(self._obje)
        self.canvas().plotter.remove_actor(self._mesh_points)

    def _setColor(self, color, type):
        if type == "color":
            c = QtGui.QColor(color)
            if self._type == "scalars":
                self.canvas().plotter.remove_actor(self._obj)
                self._obj = self.canvas().plotter.add_mesh(self._mesh, color=[c.redF(), c.greenF(), c.blueF()], line_width=4)
            else:
                self._obj.GetProperty().SetColor([c.redF(), c.greenF(), c.blueF()])
            self._type = "color"
        if type == "scalars":
            self.canvas().plotter.remove_actor(self._obj)
            self._obj = self.canvas().plotter.add_mesh(self._mesh, scalars = self._wave.data, line_width=4, cmap=color)
            self._type = "scalars"

    def _setVisible(self, visible):
        self._obj.visibility = visible
        if visible:
            if self._obje is not None:
                self._obje.visibility = self.edgesVisible()
            self._mesh_points.visibility = self.meshesVisible()
        else:
            if self._obje is not None:
                self._obje.visibility = False
            self._mesh_points.visibility = False

    def _showEdges(self, b):
        if self._obje is not None:
            self._obje.visibility = b

    def _showMeshes(self, b):
        self._mesh_points.visibility = b

    def rayTrace(self, start, end):
        x0, x1 = start, (end - start) / np.linalg.norm(end - start)
        res, d_min = [], None
        for y0, y1 in zip(self._p0, self._p1 - self._p0):
            pos, d = self._findNearest(x0, x1, y0, y1)
            if d is None:
                continue
            if np.arctan(d / np.linalg.norm(pos - x0)) * 180 / 3.1415 > 2:
                continue
            elif d_min is None:
                res, d_min = pos, d
            elif d < d_min:
                res, d_min = pos, d
        return res

    def _findNearest(self, x0, x1, y0, y1):
        Ai = np.linalg.inv([[x1.dot(x1), -x1.dot(y1)], [x1.dot(y1), -y1.dot(y1)]])
        t, s = Ai.dot([(y0 - x0).dot(x1), (y0 - x0).dot(y1)])
        if t < 0:
            return None, None
        if s < 0 or s > 1:
            return None, None
        p1, p2 = x0 + t * x1, y0 + s * y1
        return p2, np.linalg.norm(p2 - p1)


class _pyvistaPoint(PointData):
    """Implementation of LineData for matplotlib"""

    def __init__(self, canvas, wave):
        super().__init__(canvas, wave)
        self._wave = wave
        self._obj = canvas.plotter.add_points(wave.x.astype(float), scalars=wave.data, render_points_as_spheres=True, point_size=17, color="k")
        self._type = "scalars"

    def remove(self):
        self.canvas().plotter.remove_actor(self._obj)

    def _setColor(self, color, type):
        if type == "color":
            c = QtGui.QColor(color)
            if self._type == "scalars":
                self.canvas().plotter.remove_actor(self._obj)
                self._obj = self.canvas().plotter.add_points(self._wave.x.astype(float), color=[c.redF(), c.greenF(), c.blueF()], render_points_as_spheres=True, point_size=17)
            else:
                self._obj.GetProperty().SetColor([c.redF(), c.greenF(), c.blueF()])
            self._type = "color"
        if type == "scalars":
            self.canvas().plotter.remove_actor(self._obj)
            self._obj = self.canvas().plotter.add_points(self._wave.x.astype(float), cmap=color, render_points_as_spheres=True, point_size=17)
            self._type = "scalars"

    def rayTrace(self, start, end):
        x0, v = start, (end - start) / np.linalg.norm(end - start)  # line y = x0 + tv
        d = self._wave.x - x0
        t_c = d.dot(v)
        dist = [np.linalg.norm(d - t * v) for t in t_c]
        i = np.argmin(dist)
        if np.arctan(np.linalg.norm(dist[i]) / np.linalg.norm(t_c[i] * v)) * 180 / 3.1415 > 2:
            return []
        return [self._wave.x[i]]

    def _updateData(self):
        return

    def _setVisible(self, visible):
        self._obj.visibility=visible


class _pyvistaData(CanvasData3D):
    def _appendVolume(self, wave):
        return _pyvistaVolume(self.canvas(), wave)

    def _appendSurface(self, wave):
        return _pyvistaSurface(self.canvas(), wave)

    def _appendLine(self, wave):
        return _pyvistaLine(self.canvas(), wave)

    def _appendPoint(self, wave):
        return _pyvistaPoint(self.canvas(), wave)

    def _rayTrace(self, data, start, end):
        return data.rayTrace(start, end)

    def _remove(self, data):
        data.remove()
