import warnings
import io
import numpy as np

from lys import Wave, filters
from lys.Qt import QtCore
from lys.errors import NotImplementedWarning

from .CanvasBase import CanvasPart3D, saveCanvas
from .WaveData import WaveData3D
from .Volume import VolumeData
from .Surface import SurfaceData
from .Line import LineData
from .Point import PointData


class CanvasData3D(CanvasPart3D):
    dataChanged = QtCore.pyqtSignal()
    """pyqtSignal that is emittd when data is added/removed/changed."""

    dataCleared = QtCore.pyqtSignal()
    """Emitted when clear method is called"""

    def __init__(self, canvas):
        super().__init__(canvas)
        self._Datalist = []
        canvas.saveCanvas.connect(self._save)
        canvas.loadCanvas.connect(self._load)

    @saveCanvas
    def append(self, wave, appearance={}, filter=None):
        """
        Append Wave to canvas.

        Args:
            wave(Wave): The data to be added.
            appearance(dict): The dictionary that determins appearance. See :meth:`.WaveData3D.saveAppearance` for detail.
            filter(filter): See :meth:`.WaveData3D.setFilter`

        Returns:
            WaveData3D: The object from which users can modify the data in graph.
        """
        func = {"point": self._appendPoint, "line": self._appendLine, "volume": self._appendVolume, "surface": self._appendSurface}
        # When multiple data is passed
        if isinstance(wave, list) or isinstance(wave, tuple):
            return [self.append(ww) for ww in wave]
        # Update
        if isinstance(wave, WaveData3D):
            return self.append(wave.getWave(),
                               appearance=wave.saveAppearance(),
                               filter=wave.getFilter())
        type = self.__checkType(wave)
        obj = func[type](wave)
        obj.setFilter(filter)
        obj.loadAppearance(appearance)
        obj.modified.connect(self.dataChanged)
        self._Datalist.append(obj)
        self.dataChanged.emit()
        return obj

    def __checkType(self, wav):
        if "tetra" in wav.note["elements"].keys():
            return "volume"
        if "hexa" in wav.note["elements"].keys():
            return "volume"
        if "pyramid" in wav.note["elements"].keys():
            return "volume"
        if "prism" in wav.note["elements"].keys():
            return "volume"
        elif "triangle" in wav.note["elements"].keys():
            return "surface"
        elif "quad" in wav.note["elements"].keys():
            return "surface"
        elif "line" in wav.note["elements"].keys():
            return "line"
        elif "point" in wav.note["elements"].keys():
            return "point"
        raise RuntimeError("[Graph] Can't append this data. shape = " + str(wav.data.shape))

    @ saveCanvas
    def remove(self, obj):
        """
        Remove data from canvas.

        Args:
            obj(WaveData): WaveData object to be removed.
        """
        if hasattr(obj, '__iter__'):
            for o in obj:
                self.remove(o)
            return
        self._remove(obj)
        self._Datalist.remove(obj)
        obj.modified.disconnect(self.dataChanged)
        self.dataChanged.emit()

    @ saveCanvas
    def clear(self):
        """
        Remove all data from canvas.
        """
        while len(self._Datalist) != 0:
            self.remove(self._Datalist[0])
        self.dataCleared.emit()

    def getWaveData(self, type="all"):
        """
        Return list of WaveData object that is specified by *type*.

        Args:
            type('all', 'line', 'image', 'rgb', 'vector', or 'contour'): The data type to be returned.
        """
        if type == "all":
            return self._Datalist
        elif type == "volume":
            return [data for data in self._Datalist if isinstance(data, VolumeData)]
        elif type == "surface":
            return [data for data in self._Datalist if isinstance(data, SurfaceData)]
        elif type == "line":
            return [data for data in self._Datalist if isinstance(data, LineData)]
        elif type == "point":
            return [data for data in self._Datalist if isinstance(data, PointData)]

    def getVolume(self):
        """
        Return all VolumeData in the canvas.
        """
        return self.getWaveData("volume")

    def getSurface(self):
        """
        Return all SurfaceData in the canvas.
        """
        return self.getWaveData("surface")

    def getLine(self):
        """
        Return all LineData in the canvas.
        """
        return self.getWaveData("line")

    def getPoint(self):
        """
        Return all PointData in the canvas.
        """
        return self.getWaveData("point")

    def rayTrace(self, start, end, type="all"):
        data = self.getWaveData(type)
        distance = np.linalg.norm(end - start)
        for d in data:
            if not d.getVisible():
                continue
            point = self._rayTrace(d, start, end)
            if len(point) == 0:
                continue
            if np.linalg.norm(point - start) < distance:
                distance = np.linalg.norm(point - start)
                res = d
        return res

    def _save(self, dictionary):
        dic = {}
        for i, data in enumerate(self._Datalist):
            dic[i] = {}
            b = io.BytesIO()
            data.getWave().export(b)
            dic[i]['Wave_npz'] = b.getvalue()
            dic[i]['Appearance'] = str(data.saveAppearance())
            if data.getFilter() is None:
                dic[i]['Filter'] = None
            else:
                dic[i]['Filter'] = filters.toString(data.getFilter())
        dictionary['Datalist'] = dic

    def _load(self, dictionary):
        if 'Datalist' in dictionary:
            self.clear()
            dic = dictionary['Datalist']
            i = 0
            while i in dic:
                w = Wave(io.BytesIO(dic[i]['Wave_npz']))
                obj = self.append(w)
                self.__loadMetaData(obj, dic[i])
                i += 1

    def __loadMetaData(self, obj, d):
        filter = d.get('Filter', None)
        if filter is not None:
            obj.setFilter(filters.fromString(filter))
        if 'Appearance' in d:
            obj.loadAppearance(eval(d['Appearance']))

    def _remove(self, data):
        raise NotImplementedError(str(type(self)) + " does not implement _remove(data) method.")

    def _appendVolume(self, wave):
        warnings.warn(str(type(self)) + " does not implement _appendVolume(wave) method.", NotImplementedWarning)

    def _appendSurface(self, wave):
        warnings.warn(str(type(self)) + " does not implement _appendSurface(wave) method.", NotImplementedWarning)

    def _appendLine(self, wave):
        warnings.warn(str(type(self)) + " does not implement _appendLine(wave) method.", NotImplementedWarning)

    def _appendPoint(self, wave):
        warnings.warn(str(type(self)) + " does not implement _appendPoint(wave) method.", NotImplementedWarning)

    def _rayTrace(self, data, start, end):
        warnings.warn(str(type(self)) + " does not implement _rayTrace(data) method.", NotImplementedWarning)
