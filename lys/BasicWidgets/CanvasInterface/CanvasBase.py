import os
import io
from matplotlib.colors import hsv_to_rgb
from .SaveCanvas import *
from . import LineData, ImageData, RGBData, VectorData, ContourData
from lys import *
from lys import load, Wave, filters
import _pickle as cPickle
import numpy as np


class CanvasBaseBase(DrawableCanvasBase):
    dataChanged = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._Datalist = []
        self.__loadFlg = False

    @notSaveCanvas
    def emitCloseEvent(self, *args, **kwargs):
        self.Clear()
        super().emitCloseEvent()

    @saveCanvas
    def _onWaveModified(self, d):
        if self.__loadFlg:
            return
        self.Remove(d)
        self._Append(d.wave, d.axis, d.id, appearance=d.appearance, offset=d.offset, contour=isinstance(d, ContourData), filter=d.filter, vector=isinstance(d, VectorData))

    @saveCanvas
    def Append(self, wave, axis="BottomLeft", id=None, appearance=None, offset=(0, 0, 0, 0), contour=False, filter=None, vector=False):
        if isinstance(wave, list):
            for w in wave:
                self.Append(w, axis=axis, appearance=appearance, offset=offset, contour=contour, filter=filter, vector=vector)
            return
        if isinstance(wave, Wave):
            wav = wave
        else:
            wav = load(wave)
        if appearance is None:
            appearance = {}
        return self._Append(wav, axis, id, dict(appearance), offset, contour=contour, filter=filter, vector=vector)

    @saveCanvas
    def _Append(self, w, axis, id, appearance, offset, contour=False, filter=None, vector=False):
        func = {"line": self._append1d, "vector": self._appendVectorField, "image": self._append2d, "contour": self._appendContour}
        func["rgb"] = lambda w, ax: self._append3d(self._makeRGBData(w, appearance), ax)
        id_def = {"line": 2000, "vector": 5500, "image": 5000, "contour": 4000, "rgb": 6000}

        type = self._checkType(w, contour, vector)
        filtered = self._filteredWave(w, offset, filter)
        ids = -id_def[type] + len(self.getWaveData(type))
        obj = func[type](filtered, axis)
        # obj.setZ(ids)
        obj.setMetaData(w, axis, ids, appearance=appearance, offset=offset, zindex=ids, filter=filter, filteredWave=filtered)
        self._Datalist.append(obj)
        obj.modified.connect(self._onWaveModified)
        self.dataChanged.emit()
        if appearance is not None:
            self.__loadFlg = True
            obj.loadAppearance(appearance)
            self.__loadFlg = False
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

    def _filteredWave(self, w, offset, filter):
        if filter is None:
            filt = filters.Filters([filters.OffsetFilter(offset)])
        else:
            filt = filter + filters.OffsetFilter(offset)
        return filt.execute(w)

    def _makeRGBData(self, wav, appearance):
        wav = wav.duplicate()
        if wav.data.ndim == 2:
            if 'Range' in appearance:
                rmin, rmax = appearance['Range']
            else:
                rmin, rmax = 0, np.max(np.abs(wav.data))
            wav.data = self._Complex2HSV(wav.data, rmin, rmax, appearance.get('ColorRotation', 0))
        elif wav.data.ndim == 3:
            if 'Range' in appearance:
                rmin, rmax = appearance['Range']
                amp = np.where(wav.data < rmin, rmin, wav.data)
                amp = np.where(amp > rmax, rmax, amp)
                wav.data = (amp - rmin) / (rmax - rmin)
        return wav

    def _Complex2HSV(self, z, rmin, rmax, hue_start=0):
        amp = np.abs(z)
        amp = np.where(amp < rmin, rmin, amp)
        amp = np.where(amp > rmax, rmax, amp)
        ph = np.angle(z, deg=1) + hue_start
        h = (ph % 360) / 360
        s = np.ones_like(h)
        v = (amp - rmin) / (rmax - rmin)
        rgb = hsv_to_rgb(np.dstack((h, s, v)))
        return rgb

    @saveCanvas
    def Remove(self, obj):
        if hasattr(obj, '__iter__'):
            for o in obj:
                self.Remove(o)
            return
        self._remove(obj)
        self._Datalist.remove(obj)
        obj.modified.disconnect(self._onWaveModified)
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
        i = 0
        dic = {}
        for data in self._Datalist:
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
            i += 1
        dictionary['Datalist'] = dic

    def LoadFromDictionary(self, dictionary, path):
        axisDict = {1: "BottomLeft", 2: "TopLeft", 3: "BottomRight", 4: "TopRight", "BottomLeft": "BottomLeft", "TopLeft": "TopLeft", "BottomRight": "BottomRight", "TopRight": "TopRight"}
        i = 0
        sdir = os.getcwd()
        os.chdir(path)
        if 'Datalist' in dictionary:
            dic = dictionary['Datalist']
            while i in dic:
                w = dic[i]['File']
                if w is None:
                    if 'Wave' in dic[i]:  # for backward compability
                        waveData = dic[i]['Wave']
                        waveData = waveData.replace(b'ExtendAnalysis.core', b'lys.core')
                        waveData = waveData.replace(b'ExtendAnalysis.ExtendType', b'lys.core')
                        waveData = waveData.replace(b'produce', b'_produceWave')
                        w = cPickle.loads(waveData)
                    elif 'Wave_npz' in dic[i]:
                        w = Wave(io.BytesIO(dic[i]['Wave_npz']))
                axis = axisDict[dic[i]['Axis']]
                if 'Appearance' in dic[i]:
                    ap = eval(dic[i]['Appearance'])
                else:
                    ap = {}
                if 'Offset' in dic[i]:
                    offset = eval(dic[i]['Offset'])
                else:
                    offset = (0, 0, 0, 0)
                contour = dic[i].get('Contour', False)
                vector = dic[i].get('Vector', False)
                if 'Filter' in dic[i]:
                    str = dic[i]['Filter']
                    if str is None:
                        filter = None
                    else:
                        filter = filters.fromString(dic[i]['Filter'])
                else:
                    filter = None
                self.Append(w, axis, appearance=ap, offset=offset, contour=contour, filter=filter, vector=vector)
                i += 1
        os.chdir(sdir)

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
