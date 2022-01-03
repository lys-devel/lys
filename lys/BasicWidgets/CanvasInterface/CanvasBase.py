import io
import _pickle as cPickle

from lys import *
from lys import load, Wave, filters

from .SaveCanvas import *
from . import LineData, ImageData, RGBData, VectorData, ContourData


class CanvasBaseBase(DrawableCanvasBase):
    _id_def = {"line": 2000, "vector": 5500, "image": 5000, "contour": 4000, "rgb": 6000}
    dataChanged = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._Datalist = []

    @notSaveCanvas
    def emitCloseEvent(self, *args, **kwargs):
        self.Clear()
        super().emitCloseEvent()

    @saveCanvas
    def Append(self, w, axis="BottomLeft", appearance={}, offset=(0, 0, 0, 0), filter=None, contour=False, vector=False):
        func = {"line": self._append1d, "vector": self._appendVectorField, "image": self._append2d, "contour": self._appendContour, "rgb": self._append3d}
        if isinstance(w, list) or isinstance(w, tuple):
            return [self.Append(ww, axis=axis, contour=contour, vector=vector) for ww in w]
        type = self._checkType(w, contour, vector)
        obj = func[type](w, axis)
        obj.setOffset(offset)
        obj.setFilter(filter)
        # obj.setZ(-id_def[type] + len(self.getWaveData(type)))
        obj.loadAppearance(appearance)
        obj.modified.connect(self.dataChanged)
        self._Datalist.append(obj)
        self.dataChanged.emit()
        return obj

    def _checkType(self, wav, contour, vector):
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

    @saveCanvas
    def Remove(self, obj):
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
        while len(self._Datalist) != 0:
            self.Remove(self._Datalist[0])

    def getWaveData(self, type="all"):
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
        return self.getWaveData("line")

    def getImages(self):
        return self.getWaveData("image")

    def getContours(self):
        return self.getWaveData("contour")

    def getRGBs(self):
        return self.getWaveData("rgb")

    def getVectorFields(self):
        return self.getWaveData("vector")

    def SaveAsDictionary(self, dictionary, path):
        dic = {}
        for i, data in enumerate(self._Datalist):
            dic[i] = {}
            dic[i]['File'] = None
            b = io.BytesIO()
            data.wave.export(b)
            dic[i]['Wave_npz'] = b.getvalue()
            dic[i]['Axis'] = data.axis
            dic[i]['Appearance'] = str(data.appearance)
            dic[i]['Offset'] = str(data.offset)
            dic[i]['Contour'] = isinstance(data, ContourData)
            dic[i]['Vector'] = isinstance(data, VectorData)
            if data.filter is None:
                dic[i]['Filter'] = None
            else:
                dic[i]['Filter'] = str(data.filter)
        dictionary['Datalist'] = dic

    def LoadFromDictionary(self, dictionary, path):
        axisDict = {1: "BottomLeft", 2: "TopLeft", 3: "BottomRight", 4: "TopRight", "BottomLeft": "BottomLeft", "TopLeft": "TopLeft", "BottomRight": "BottomRight", "TopRight": "TopRight"}
        i = 0
        if 'Datalist' in dictionary:
            dic = dictionary['Datalist']
            while i in dic:
                w = self.__loadWave(dic[i])
                axis = axisDict[dic[i]['Axis']]
                ap = eval(dic[i].get('Appearance', "dict()"))
                offset = eval(dic[i].get('Offset', "(0,0,0,0)"))
                contour = dic[i].get('Contour', False)
                vector = dic[i].get('Vector', False)
                filter = dic[i].get('Filter', None)
                if filter is not None:
                    filter = filters.fromString(filter)
                self.Append(w, axis, appearance=ap, offset=offset, filter=filter, contour=contour, vector=vector)
                i += 1

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
        raise NotImplementedError()

    def _append1d(self, wave, axis):
        raise NotImplementedError()

    def _append2d(self, wave, axis):
        raise NotImplementedError()

    def _append3d(self, wave, axis):
        raise NotImplementedError()

    def _appendContour(self, wave, axis):
        raise NotImplementedError()

    def _appendVectorField(self, wav, axis):
        raise NotImplementedError()
