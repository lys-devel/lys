import warnings
import io
import numpy as np
import _pickle as cPickle

from lys import Wave, filters, load
from lys.Qt import QtCore
from lys.errors import NotImplementedWarning, suppressLysWarnings

from .CanvasBase import CanvasPart, saveCanvas
from .WaveData import WaveData
from .Line import LineData
from .Image import ImageData
from .RGB import RGBData
from .Vector import VectorData
from .Contour import ContourData


class CanvasData(CanvasPart):
    dataChanged = QtCore.pyqtSignal()
    """pyqtSignal that is emittd when data is added/removed/changed."""

    def __init__(self, canvas):
        super().__init__(canvas)
        self._Datalist = []
        canvas.saveCanvas.connect(self._save)
        canvas.loadCanvas.connect(self._load)

    @suppressLysWarnings
    @saveCanvas
    def Append(self, wave, axis="BottomLeft", appearance={}, offset=(0, 0, 0, 0), filter=None, contour=False, vector=False):
        """
        Append Wave to graph.

        Data type is determined by the shape and dtype of wave in addition to *contour* and *vector*.

        When 1-dimensional data is added, line is added to the graph.

        When 2-dimensional real data is added and *contour* is False, image is added.

        When 2-dimensional real data is added and *contour* is True, contour is added.

        When 2-dimensional complex data is added and *vector* is False, it is converted to RGB colormap data.

        When 2-dimensional complex data is added and *vector* is True, it is added as vector map.

        When 3-dimensional data is added and its shape[2] is 3 or 4, it is added as RGB(A) color map data.

        See :class:`.Line.LineData`, :class:`.Image.ImageData`, :class:`Contour.ContourData`, :class:`.Vector.VectorData`, :class:`.RGB.RGBData` for detail of each data type.

        Args:
            wave(Wave): The data to be added.
            axis('BottomLeft', 'BottomRight', 'TopLeft', or 'TopRight'): The axis to which the data is added.
            appearance(dict): The dictionary that determins appearance. See :meth:`.WaveData.saveAppearance` for detail.
            offset(tuple  of length 4): See :meth:`.WaveData.setOffset`
            filter(filter): See :meth:`.WaveData.setFilter`
            contour(bool): See above description.
            vector(bool): See above description.

        """
        func = {"line": self._append1d, "vector": self._appendVectorField, "image": self._append2d, "contour": self._appendContour, "rgb": self._append3d}
        if isinstance(wave, list) or isinstance(wave, tuple):
            return [self.Append(ww, axis=axis, contour=contour, vector=vector) for ww in wave]
        if isinstance(wave, WaveData):
            return self.Append(wave.getWave(),
                               axis=wave.getAxis(),
                               appearance=wave.saveAppearance(),
                               offset=wave.getOffset(),
                               filter=wave.getFilter(),
                               contour=isinstance(wave, ContourData),
                               vector=isinstance(wave, VectorData))
        self.__addAxes(axis)
        type = self.__checkType(wave, contour, vector)
        obj = func[type](wave, axis)
        obj.setOffset(offset)
        obj.setFilter(filter)
        obj.setZOrder(self.__getDefaultZ(type))
        obj.loadAppearance(appearance)
        obj.modified.connect(self.dataChanged)
        self._Datalist.append(obj)
        self.dataChanged.emit()
        return obj

    def __addAxes(self, axis):
        if axis in ["BottomRight", "TopRight"]:
            self.canvas().addAxis("Right")
        if axis in ["TopLeft", "TopRight"]:
            self.canvas().addAxis("Top")

    def __checkType(self, wav, contour, vector):
        if wav.data.ndim == 1:
            return "line"
        elif wav.data.ndim == 2:
            if wav.data.dtype == complex:
                if vector:
                    return "vector"
                else:
                    return "rgb"
            else:
                if contour:
                    return "contour"
                else:
                    return "image"
        elif wav.data.ndim == 3:
            if wav.data.shape[2] in [3, 4]:
                return "rgb"
        raise RuntimeError("[Graph] Can't append this data. shape = " + str(wav.data.shape))

    def __getDefaultZ(self, type):
        id_def = {"line": 8000, "image": 2000, "vector": 6000, "contour": 4000, "rgb": 3000}
        data = self.getWaveData(type)
        return np.max([d.getZOrder() for d in data] + [id_def[type]]) + 1

    @ saveCanvas
    def Remove(self, obj):
        """
        Remove data from canvas.

        Args:
            obj(WaveData): WaveData object to be removed.
        """
        if hasattr(obj, '__iter__'):
            for o in obj:
                self.Remove(o)
            return
        self._remove(obj)
        self._Datalist.remove(obj)
        obj.modified.disconnect(self.dataChanged)
        self.dataChanged.emit()

    @ saveCanvas
    def Clear(self):
        """
        Remove all data from canvas.
        """
        while len(self._Datalist) != 0:
            self.Remove(self._Datalist[0])

    def getWaveData(self, type="all"):
        """
        Return list of WaveData object that is specified by *type*.

        Args:
            type('all', 'line', 'image', 'rgb', 'vector', or 'contour'): The data type to be returned.
        """
        if type == "all":
            return self._Datalist
        elif type == "line":
            return [data for data in self._Datalist if isinstance(data, LineData)]
        elif type == "image":
            return [data for data in self._Datalist if isinstance(data, ImageData)]
        if type == "rgb":
            return [data for data in self._Datalist if isinstance(data, RGBData)]
        if type == "vector":
            return [data for data in self._Datalist if isinstance(data, VectorData)]
        if type == "contour":
            return [data for data in self._Datalist if isinstance(data, ContourData)]

    def getLines(self):
        """
        Return all LineData in the canvas.
        """
        return self.getWaveData("line")

    def getImages(self):
        """
        Return all ImageData in the canvas.
        """
        return self.getWaveData("image")

    def getContours(self):
        """
        Return all ContourData in the canvas.
        """
        return self.getWaveData("contour")

    def getRGBs(self):
        """
        Return all RGBData in the canvas.
        """
        return self.getWaveData("rgb")

    def getVectorFields(self):
        """
        Return all VectorData in the canvas.
        """
        return self.getWaveData("vector")

    def _save(self, dictionary):
        dic = {}
        for i, data in enumerate(self._Datalist):
            dic[i] = {}
            dic[i]['File'] = None
            b = io.BytesIO()
            data.getWave().export(b)
            dic[i]['Wave_npz'] = b.getvalue()
            dic[i]['Axis'] = data.getAxis()
            dic[i]['Appearance'] = str(data.saveAppearance())
            dic[i]['Offset'] = str(data.getOffset())
            dic[i]['ZOrder'] = data.getZOrder()
            dic[i]['Contour'] = isinstance(data, ContourData)
            dic[i]['Vector'] = isinstance(data, VectorData)
            if data.getFilter() is None:
                dic[i]['Filter'] = None
            else:
                dic[i]['Filter'] = filters.toString(data.getFilter())
        dictionary['Datalist'] = dic

    def _load(self, dictionary):
        axisDict = {1: "BottomLeft", 2: "TopLeft", 3: "BottomRight", 4: "TopRight", "BottomLeft": "BottomLeft", "TopLeft": "TopLeft", "BottomRight": "BottomRight", "TopRight": "TopRight"}
        if 'Datalist' in dictionary:
            self.Clear()
            dic = dictionary['Datalist']
            i = 0
            while i in dic:
                w = self.__loadWave(dic[i])
                axis = axisDict[dic[i]['Axis']]
                contour = dic[i].get('Contour', False)
                vector = dic[i].get('Vector', False)
                obj = self.Append(w, axis, contour=contour, vector=vector)
                self.__loadMetaData(obj, dic[i])
                i += 1

    def __loadMetaData(self, obj, d):
        if 'ZOrder' in d:
            obj.setZOrder(d['ZOrder'])
        if 'Offset' in d:
            obj.setOffset(eval(d['Offset']))
        filter = d.get('Filter', None)
        if filter is not None:
            obj.setFilter(filters.fromString(filter))
        if 'Appearance' in d:
            obj.loadAppearance(eval(d['Appearance']))

    def __loadWave(self, d):
        w = d['File']
        if w is None:
            if 'Wave' in d:  # for backward compability
                waveData = d['Wave']
                waveData = waveData.replace(b'ExtendAnalysis.core', b'lys.core')
                waveData = waveData.replace(b'ExtendAnalysis.ExtendType', b'lys.core')
                waveData = waveData.replace(b'produce', b'_produceWave')
                w = cPickle.loads(waveData)
            elif 'Wave_npz' in d:
                w = Wave(io.BytesIO(d['Wave_npz']))
        else:
            w = load(w)
        return w

    def _remove(self, data):
        raise NotImplementedError(str(type(self)) + " does not implement _remove(data) method.")

    def _append1d(self, wave, axis):
        warnings.warn(str(type(self)) + " does not implement _append1d(wave, axis) method.", NotImplementedWarning)

    def _append2d(self, wave, axis):
        warnings.warn(str(type(self)) + " does not implement _append2d(wave, axis) method.", NotImplementedWarning)

    def _append3d(self, wave, axis):
        warnings.warn(str(type(self)) + " does not implement _append3d(wave, axis) method.", NotImplementedWarning)

    def _appendContour(self, wave, axis):
        warnings.warn(str(type(self)) + " does not implement _appendContour(wave, axis) method.", NotImplementedWarning)

    def _appendVectorField(self, wav, axis):
        warnings.warn(str(type(self)) + " does not implement _appendVectorField(wave, axis) method.", NotImplementedWarning)
