from enum import IntEnum
from matplotlib.colors import hsv_to_rgb
from .SaveCanvas import *
from ExtendAnalysis import *
from ExtendAnalysis import LoadFile
import _pickle as cPickle


class Axis(IntEnum):
    BottomLeft = 1
    TopLeft = 2
    BottomRight = 3
    TopRight = 4


class WaveData(object):
    def __init__(self, wave, obj, axes, axis, idn, appearance, offset=(0, 0, 0, 0), zindex=0, contour=False, filter=None, filteredWave=None, vector=False):
        self.wave = wave
        self.obj = obj
        self.axis = axis
        self.axes = axes
        self.id = idn
        self.appearance = appearance
        self.offset = offset
        self.zindex = zindex
        self.contour = contour
        self.vector = vector
        self.filter = filter
        self.filteredWave = filteredWave


class CanvasBaseBase(DrawableCanvasBase):
    dataChanged = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._Datalist = []
        self._inverted = False

    @notSaveCanvas
    def emitCloseEvent(self, *args, **kwargs):
        self.Clear()
        super().emitCloseEvent()

    @saveCanvas
    def updateAll(self):
        for d in self._Datalist:
            self.OnWaveModified(d.wave)

    @saveCanvas
    def OnWaveModified(self, wave):
        self.saveAppearance()
        for d in self._Datalist:
            if wave == d.wave:
                self.Remove(d.id, reuse=True)
                self._Append(wave, d.axis, d.id, appearance=d.appearance, offset=d.offset, zindex=d.zindex, reuse=True, contour=d.contour, filter=d.filter, wdata=d, vector=d.vector)
                flg = True
        self.loadAppearance()

    @saveCanvas
    def Append(self, wave, axis=Axis.BottomLeft, id=None, appearance=None, offset=(0, 0, 0, 0), zindex=0, contour=False, filter=None, vector=False):
        if isinstance(wave, list):
            for w in wave:
                self.Append(w, axis=axis, appearance=appearance, offset=offset, contour=contour, filter=filter, vector=vector)
            return
        if isinstance(wave, Wave):
            wav = wave
        else:
            wav = LoadFile.load(wave)
        if appearance is None:
            ids = self._Append(wav, axis, id, {}, offset, zindex, contour=contour, filter=filter, vector=vector)
        else:
            ids = self._Append(wav, axis, id, dict(appearance), offset, zindex, contour=contour, filter=filter, vector=vector)
        return ids

    @saveCanvas
    def _Append(self, w, axis, id, appearance, offset, zindex=0, reuse=False, contour=False, filter=None, wdata=None, vector=False):
        def makeWaveData(reuse, w, obj, ax, axis, ids, appearance, offset, contour, filter, filteredWave, wdata, vector):
            if reuse:
                wdata.id = ids
                wdata.obj = obj
                wdata.axes = ax
                wdata.filteredWave = filteredWave
                return wdata
            else:
                wd = WaveData(w, obj, ax, axis, ids, appearance, offset, contour=contour, filter=filter, filteredWave=filteredWave, vector=vector)
                return wd
        if filter is not None:
            wav = w.Duplicate()
            filter.execute(wav)
        else:
            wav = w
        filteredWave = wav
        type = self._checkType(w, contour, vector)
        if type == "rgb":
            wav = self._makeRGBData(wav, appearance)
        if self._inverted:
            wav = self._makeInvertedData(wav)
        f = self._getAppendFunc(type)
        if f is None:
            print("[Graph] Can't append this data. shape = ", w.data.shape)
            return
        ids, obj, ax = f(wav, axis, id, appearance, offset)
        id_pos = ids + self._getDefaultId(type)
        self._Datalist.insert(id_pos, makeWaveData(reuse, w, obj, ax, axis, ids, appearance, offset, contour, filter, filteredWave, wdata, vector))
        if not reuse:
            w.modified.connect(self.OnWaveModified)
        self.dataChanged.emit()
        if appearance is not None:
            self.loadAppearance()
        return ids

    def _makeInvertedData(self, wav):
        w = wav.Duplicate()
        if w.data.ndim == 1:
            w.data, w.x = w.x, w.data
        if w.data.ndim == 2:
            w.data, w.x, w.y = w.data.T, w.y, w.x
        return w

    def _makeRGBData(self, wav, appearance):
        if wav.data.ndim == 2:
            wav = wav.Duplicate()
            if 'Range' in appearance:
                rmin, rmax = appearance['Range']
            else:
                rmin, rmax = 0, np.max(np.abs(wav.data))
            wav.data = self._Complex2HSV(wav.data, rmin, rmax, appearance.get('ColorRotation', 0))
        elif wav.data.ndim == 3:
            wav = wav.Duplicate()
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
        return "undefined"

    def _getDefaultId(self, type):
        if type == "line":
            return 2000
        if type == "vector":
            return 5500
        if type == "contour":
            return 4000
        if type == "image":
            return 5000
        if type == "rgb":
            return 6000

    def _getAppendFunc(self, type):
        if type == "line":
            return self._Append1D
        if type == "vector":
            return self._AppendVectorField
        if type == "contour":
            return self._AppendContour
        if type == "image":
            return self._Append2D
        if type == "rgb":
            return self._Append3D

    def _Append1D(self, wav, axis, ID, appearance, offset):
        if wav.x.ndim == 0:
            xdata = np.arange(len(wav.data))
            ydata = np.array(wav.data)
        else:
            xdata = np.array(wav.x)
            ydata = np.array(wav.data)
        if not offset[2] == 0.0:
            xdata = xdata * offset[2]
        if not offset[3] == 0.0:
            ydata = ydata * offset[3]
        xdata = xdata + offset[0]
        ydata = np.real(ydata + offset[1])
        if ID is None:
            id = -2000 + len(self.getLines())
        else:
            id = ID
        obj, ax = self._append1d(xdata, ydata, axis, id)
        return id, obj, ax

    def _Append2D(self, wav, axis, ID, appearance, offset):
        if ID is None:
            id = -5000 + len(self.getImages())
        else:
            id = ID
        im, ax = self._append2d(wav, offset, axis, id)
        return id, im, ax

    def _Append3D(self, wav, axis, ID, appearance, offset):
        if ID is None:
            id = -6000 + len(self.getRGBs())
        else:
            id = ID
        im, ax = self._append3d(wav, offset, axis, id)
        return id, im, ax

    def _AppendContour(self, wav, axis, ID, appearance, offset):
        if ID is None:
            id = -4000 + len(self.getContours())
        else:
            id = ID
        im, ax = self._appendContour(wav, offset, axis, id)
        return id, im, ax

    def _AppendVectorField(self, wav, axis, ID, appearance, offset):
        if ID is None:
            id = -5500 + len(self.getVectorFields())
        else:
            id = ID
        im, ax = self._appendVectorField(wav, offset, axis, id)
        return id, im, ax

    @saveCanvas
    def Remove(self, indexes, reuse=False):
        if hasattr(indexes, '__iter__'):
            list = indexes
        else:
            list = [indexes]
        for i in list:
            for d in self._Datalist:
                if i == d.id:
                    self._remove(d)
                    self._Datalist.remove(d)
                    if not reuse:
                        d.wave.modified.disconnect(self.OnWaveModified)
        self.dataChanged.emit()

    @saveCanvas
    def Clear(self):
        self.Remove([d.id for d in self._Datalist])

    def getWaveData(self, dim=None, contour=False, vector=False):
        if type(dim) == str:
            return self._getWaveDataFromType(dim)
        if dim is None:
            return self._Datalist
        res = []
        for d in self._Datalist:
            if d.wave.data.ndim == 1 and dim == 1:
                res.append(d)
            if d.wave.data.ndim == 2:
                if dim == 2:
                    if d.wave.data.dtype == complex:
                        if vector and d.vector:
                            res.append(d)
                    else:
                        if contour == d.contour and vector == d.vector:
                            res.append(d)
                if dim == 3 and d.wave.data.dtype == complex and not d.vector:
                    res.append(d)
            if d.wave.data.ndim == 3 and dim == 3:
                res.append(d)
        return res

    def _getWaveDataFromType(self, type):
        if type == "line":
            return self.getLines()
        if type == "image":
            return self.getImages()
        if type == "vector":
            return self.getVectorFields()
        if type == "rgb":
            return self.getRGBs()
        if type == "contour":
            return self.getContours()

    def getLines(self):
        return self.getWaveData(1)

    def getImages(self):
        return self.getWaveData(2)

    def getContours(self):
        return self.getWaveData(2, contour=True)

    def getRGBs(self):
        return self.getWaveData(3)

    def getVectorFields(self):
        return self.getWaveData(2, vector=True)

    def setInverted(self, b):
        self._inverted = b
        self.updateAll()

    def inverted(self):
        return self._inverted

    def getDataFromIndexes(self, dim, indexes):
        res = []
        if hasattr(indexes, '__iter__'):
            list = indexes
        else:
            list = [indexes]
        for i in list:
            for d in self.getWaveData(dim):
                if d.id == i:
                    res.append(d)
        return res

    def SaveAsDictionary(self, dictionary, path):
        i = 0
        dic = {}
        self.saveAppearance()
        for data in self._Datalist:
            dic[i] = {}
            dic[i]['File'] = None
            dic[i]['Wave'] = cPickle.dumps(data.wave)
            dic[i]['Axis'] = int(data.axis)
            dic[i]['Appearance'] = str(data.appearance)
            dic[i]['Offset'] = str(data.offset)
            dic[i]['ZIndex'] = str(data.zindex)
            dic[i]['Contour'] = data.contour
            dic[i]['Vector'] = data.vector
            if data.filter is None:
                dic[i]['Filter'] = None
            else:
                dic[i]['Filter'] = str(data.filter)
            i += 1
        dictionary['Datalist'] = dic
        dictionary['Inverted'] = self._inverted

    def LoadFromDictionary(self, dictionary, path):
        from ExtendAnalysis.Analysis.filters import Filters
        i = 0
        sdir = os.getcwd()
        os.chdir(path)
        if 'Datalist' in dictionary:
            dic = dictionary['Datalist']
            while i in dic:
                w = dic[i]['File']
                if w is None:
                    w = cPickle.loads(dic[i]['Wave'])
                axis = Axis(dic[i]['Axis'])
                if 'Appearance' in dic[i]:
                    ap = eval(dic[i]['Appearance'])
                else:
                    ap = {}
                if 'Offset' in dic[i]:
                    offset = eval(dic[i]['Offset'])
                else:
                    offset = (0, 0, 0, 0)
                if 'ZIndex' in dic[i]:
                    zi = eval(dic[i]['ZIndex'])
                if 'Contour' in dic[i]:
                    contour = dic[i]['Contour']
                else:
                    contour = False
                if 'Vector' in dic[i]:
                    vector = dic[i]['Vector']
                else:
                    vector = False
                if 'Filter' in dic[i]:
                    str = dic[i]['Filter']
                    if str is None:
                        filter = None
                    else:
                        filter = Filters.fromString(dic[i]['Filter'])
                else:
                    filter = None
                self.Append(w, axis, appearance=ap, offset=offset, zindex=zi, contour=contour, filter=filter, vector=vector)
                i += 1
        if 'Inverted' in dictionary:
            self._inverted = dictionary['Inverted']
        self.loadAppearance()
        os.chdir(sdir)

    def _remove(self, data):
        raise NotImplementedError()

    def _append1d(self, xdata, ydata, axis, zorder):
        raise NotImplementedError()

    def _append2d(self, wave, offset, axis, zorder):
        raise NotImplementedError()

    def _appendContour(self, wave, offset, axis, zorder):
        raise NotImplementedError()

    def _appendVectorField(self, wav, offset, axis, zorder):
        raise NotImplementedError()

    def _setZOrder(self, obj, z):
        raise NotImplementedError()


class DataSelectableCanvasBase(CanvasBaseBase):
    dataSelected = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.__indexes = {}

    def setSelectedIndexes(self, dim, indexes):
        if hasattr(indexes, '__iter__'):
            list = indexes
        else:
            list = [indexes]
        if dim == 1:
            self.__indexes["line"] = list
        if dim == 2:
            self.__indexes["image"] = list
        if dim == 3:
            self.__indexes["rgb"] = list
        else:
            self.__indexes[dim] = list
        self.dataSelected.emit()

    def getSelectedIndexes(self, dim):
        if dim == 1:
            return self.__indexes.get("line", [])
        if dim == 2:
            return self.__indexes.get("image", [])
        if dim == 3:
            return self.__indexes.get("rgb", [])
        return self.__indexes.get(dim, [])

    def _findIndex(self, id):
        res = -1
        for d in self._Datalist:
            if d.id == id:
                res = self._Datalist.index(d)
        return res

    def _reorder(self):
        n1 = 0
        n2 = 0
        for d in self._Datalist:
            if d.wave.data.ndim == 1:
                d.id = -2000 + n1
                n1 += 1
            if d.wave.data.ndim == 2:
                d.id = -5000 + n2
                n2 += 1
            self._setZOrder(d.obj, d.id)

    @saveCanvas
    def moveItem(self, list, target=None):
        tar = eval(str(target))
        for l in list:
            n = self._findIndex(l)
            item_n = self._Datalist[n]
            self._Datalist.remove(item_n)
            if tar is not None:
                self._Datalist.insert(self._findIndex(tar) + 1, item_n)
            else:
                self._Datalist.insert(0, item_n)
        self._reorder()
        self.dataChanged.emit()


class DataHidableCanvasBase(DataSelectableCanvasBase):
    def saveAppearance(self):
        super().saveAppearance()
        data = self.getWaveData()
        for d in data:
            d.appearance['Visible'] = self._isVisible(d.obj)

    def loadAppearance(self):
        super().loadAppearance()
        data = self.getWaveData()
        for d in data:
            if 'Visible' in d.appearance:
                self._setVisible(d.obj, d.appearance['Visible'])

    @saveCanvas
    def hideData(self, dim, indexes):
        dat = self.getDataFromIndexes(dim, indexes)
        for d in dat:
            self._setVisible(d.obj, False)

    @saveCanvas
    def showData(self, dim, indexes):
        dat = self.getDataFromIndexes(dim, indexes)
        for d in dat:
            self._setVisible(d.obj, True)

    def _isVisible(self, obj):
        raise NotImplementedError()

    def _setVisible(self, obj, b):
        raise NotImplementedError()


class OffsetAdjustableCanvasBase(DataHidableCanvasBase):
    @saveCanvas
    def setOffset(self, offset, indexes):
        data = self.getDataFromIndexes(None, indexes)
        print(indexes, data)
        for d in data:
            d.offset = offset
            self.OnWaveModified(d.wave)

    def getOffset(self, indexes):
        res = []
        data = self.getDataFromIndexes(None, indexes)
        for d in data:
            res.append(d.offset)
        return res
