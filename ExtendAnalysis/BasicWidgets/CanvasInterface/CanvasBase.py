from enum import IntEnum
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
    def __init__(self, wave, obj, axes, axis, idn, appearance, offset=(0, 0, 0, 0), zindex=0, contour=False):
        self.wave = wave
        self.obj = obj
        self.axis = axis
        self.axes = axes
        self.id = idn
        self.appearance = appearance
        self.offset = offset
        self.zindex = zindex
        self.contour = contour


class CanvasBaseBase(DrawableCanvasBase):
    dataChanged = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._Datalist = []

    @saveCanvas
    def OnWaveModified(self, wave):
        flg = False
        self.EnableDraw(False)
        self.saveAppearance()
        for d in self._Datalist:
            if wave.obj == d.wave.obj:
                self.Remove(d.id)
                self._Append(wave, d.axis, d.id, appearance=d.appearance, offset=d.offset, zindex=d.zindex, reuse=True, contour=d.contour)
                flg = True
        self.loadAppearance()
        self.EnableDraw(True)
        if(flg):
            self.draw()

    def Append(self, wave, axis=Axis.BottomLeft, id=None, appearance=None, offset=(0, 0, 0, 0), zindex=0, contour=False):
        if isinstance(wave, Wave):
            wav = wave
        else:
            wav = LoadFile.load(wave)
        if appearance is None:
            ids = self._Append(wav, axis, id, {}, offset, zindex, contour=contour)
        else:
            ids = self._Append(wav, axis, id, dict(appearance), offset, zindex, contour=contour)
        return ids

    @saveCanvas
    def _Append(self, wav, axis, id, appearance, offset, zindex=0, reuse=False, contour=False):
        if wav.data.ndim == 1:
            ids = self._Append1D(wav, axis, id, appearance, offset)
        if wav.data.ndim == 2:
            if contour:
                ids = self._AppendContour(wav, axis, id, appearance, offset)
            else:
                ids = self._Append2D(wav, axis, id, appearance, offset)
        if not reuse:
            wav.addModifiedListener(self.OnWaveModified)
        self.dataChanged.emit()
        if appearance is not None:
            self.loadAppearance()
        return ids

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
        ydata = ydata + offset[1]
        if ID is None:
            id = -2000 + len(self.getLines())
        else:
            id = ID
        obj, ax = self._append1d(xdata, ydata, axis, id)
        self._Datalist.insert(id + 2000, WaveData(wav, obj, ax, axis, id, appearance, offset))
        return id

    def _Append2D(self, wav, axis, ID, appearance, offset):
        if ID is None:
            id = -5000 + len(self.getImages())
        else:
            id = ID
        im, ax = self._append2d(wav, offset, axis, id)
        d = WaveData(wav, im, ax, axis, id, appearance, offset)
        self._Datalist.insert(id + 5000, d)
        return id

    def _AppendContour(self, wav, axis, ID, appearance, offset):
        if ID is None:
            id = -4000 + len(self.getContours())
        else:
            id = ID
        im, ax = self._appendContour(wav, offset, axis, id)
        d = WaveData(wav, im, ax, axis, id, appearance, offset, contour=True)
        self._Datalist.insert(id + 4000, d)
        return id

    @saveCanvas
    def Remove(self, indexes):
        if hasattr(indexes, '__iter__'):
            list = indexes
        else:
            list = [indexes]
        for i in list:
            for d in self._Datalist:
                if i == d.id:
                    self._remove(d)
                    self._Datalist.remove(d)
        self.dataChanged.emit()

    @saveCanvas
    def Clear(self):
        for d in self._Datalist:
            self.Remove(d.id)

    def getWaveData(self, dim=None, contour=False):
        if dim is None:
            return self._Datalist
        res = []
        for d in self._Datalist:
            if d.wave.data.ndim == 1 and dim == 1:
                res.append(d)
            if d.wave.data.ndim >= 2 and dim == 2 and contour == d.contour:
                res.append(d)
        return res

    def getLines(self):
        return self.getWaveData(1)

    def getImages(self):
        return self.getWaveData(2)

    def getContours(self):
        return self.getWaveData(2, True)

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
            fname = data.wave.FileName()
            if fname is not None:
                dic[i]['File'] = os.path.relpath(data.wave.FileName(), path).replace('\\', '/')
            else:
                dic[i]['File'] = None
                dic[i]['Wave'] = cPickle.dumps(data.wave)
            dic[i]['Axis'] = int(data.axis)
            dic[i]['Appearance'] = str(data.appearance)
            dic[i]['Offset'] = str(data.offset)
            dic[i]['ZIndex'] = str(data.zindex)
            dic[i]['Contour'] = data.contour
            i += 1
        dictionary['Datalist'] = dic

    def LoadFromDictionary(self, dictionary, path):
        self.EnableSave(False)
        i = 0
        sdir = pwd()
        cd(path)
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
                self.Append(w, axis, appearance=ap, offset=offset, zindex=zi, contour=contour)
                i += 1
        self.loadAppearance()
        self.EnableSave(True)
        cd(sdir)

    def _remove(self, data):
        raise NotImplementedError()

    def _append1d(self, xdata, ydata, axis, zorder):
        raise NotImplementedError()

    def _append2d(self, wave, offset, axis, zorder):
        raise NotImplementedError()

    def _appendContour(self, wave, offset, axis, zorder):
        raise NotImplementedError()

    def _setZOrder(self, obj, z):
        raise NotImplementedError()


class DataSelectableCanvasBase(CanvasBaseBase):
    dataSelected = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.__indexes = [[], [], []]

    def setSelectedIndexes(self, dim, indexes):
        if hasattr(indexes, '__iter__'):
            list = indexes
        else:
            list = [indexes]
        self.__indexes[dim] = list
        self.dataSelected.emit()

    def getSelectedIndexes(self, dim):
        return self.__indexes[dim]

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
        for d in data:
            d.offset = offset
            self.OnWaveModified(d.wave)

    def getOffset(self, indexes):
        res = []
        data = self.getDataFromIndexes(None, indexes)
        for d in data:
            res.append(d.offset)
        return res
