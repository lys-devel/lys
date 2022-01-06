import warnings
import weakref
import numpy as np

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from lys.errors import NotImplementedWarning
from .LineAnnotation import LineAnnotation, InfiniteLineAnnotation
from .SaveCanvas import *


class AnnotationData(object):
    def __init__(self, name, obj, idn, appearance):
        self.name = name
        self.obj = obj
        self.id = idn
        self.appearance = appearance
        self.axes = "BottomLeft"


class CanvasAnnotation(CanvasPart):
    _axisDict = {1: "BottomLeft", 2: "TopLeft", 3: "BottomRight", 4: "TopRight", "BottomLeft": "BottomLeft", "TopLeft": "TopLeft", "BottomRight": "BottomRight", "TopRight": "TopRight"}
    annotationChanged = pyqtSignal()

    def __init__(self, canvas):
        super().__init__(canvas)
        self._annotations = []
        self.canvas().saveCanvas.connect(self.__saveLines)
        self.canvas().loadCanvas.connect(self.__loadLines)
        self.canvas().saveCanvas.connect(self.__saveInfiniteLines)
        self.canvas().loadCanvas.connect(self.__loadInfiniteLines)

    @saveCanvas
    def addLineAnnotation(self, pos="auto", axis="BottomLeft", appearance={}):
        if pos == "auto":
            if 'Left' in axis:
                rl = self.canvas().getAxisRange('Left')
            else:
                rl = self.canvas().getAxisRange('Right')
            if 'Bottom' in axis:
                rb = self.canvas().getAxisRange('Bottom')
            else:
                rb = self.canvas().getAxisRange('Top')
            db = (np.max(rb) - np.min(rb))
            dl = (np.max(rl) - np.min(rl))
            start = (np.min(rb) + db / 2, np.min(rl) + dl / 2)
            end = (start[0] + db / 10, start[1] + dl / 10)
            pos = (start, end)
        obj = self._addLineAnnotation(pos, axis)
        obj.loadAppearance(appearance)
        self._annotations.append(obj)
        self.annotationChanged.emit()
        return obj

    def getLineAnnotations(self):
        return [annot for annot in self._annotations if isinstance(annot, LineAnnotation)]

    def __saveLines(self, dictionary):
        dic = {}
        for i, data in enumerate(self.getLineAnnotations()):
            dic[i] = {}
            pos = data.getPosition()
            dic[i]['Position0'] = list(pos[0])
            dic[i]['Position1'] = list(pos[1])
            dic[i]['Appearance'] = str(data.saveAppearance())
            dic[i]['Axis'] = data.getAxis()
        dictionary['annot_lines'] = dic

    def __loadLines(self, dictionary):
        if 'annot_lines' in dictionary:
            dic = dictionary['annot_lines']
            i = 0
            while i in dic:
                p0 = dic[i]['Position0']
                p1 = dic[i]['Position1']
                p = (p0, p1)
                appearance = eval(dic[i]['Appearance'])
                axis = self._axisDict[dic[i]['Axis']]
                obj = self.addLineAnnotation(p, axis, appearance=appearance)
                i += 1

    @saveCanvas
    def addInfiniteLineAnnotation(self, pos=None, type='vertical', axis="BottomLeft", appearance={}):
        if pos is None:
            if type == 'vertical':
                if 'Bottom' in axis:
                    r = self.canvas().getAxisRange('Bottom')
                else:
                    r = self.canvas().getAxisRange('Top')
            else:
                if 'Left' in axis:
                    r = self.canvas().getAxisRange('Left')
                else:
                    r = self.canvas().getAxisRange('Right')
            pos = np.min(r) + (np.max(r) - np.min(r)) / 2
        obj = self._addInfiniteLineAnnotation(pos, type, axis)
        self._annotations.append(obj)
        obj.loadAppearance(appearance)
        self.annotationChanged.emit()
        return obj

    def getInfiniteLineAnnotations(self):
        return [annot for annot in self._annotations if isinstance(annot, InfiniteLineAnnotation)]

    def __saveInfiniteLines(self, dictionary):
        dic = {}
        for i, data in enumerate(self.getInfiniteLineAnnotations()):
            dic[i] = {}
            pos = data.getPosition()
            dic[i]['Position'] = pos
            dic[i]['Type'] = data.getType()
            dic[i]['Appearance'] = str(data.saveAppearance())
            dic[i]['Axis'] = data.getAxis()
        dictionary['annot_infiniteLines'] = dic

    def __loadInfiniteLines(self, dictionary):
        if 'annot_infiniteLines' in dictionary:
            dic = dictionary['annot_infiniteLines']
            i = 0
            while i in dic:
                p = dic[i]['Position']
                t = dic[i]['Type']
                appearance = eval(dic[i]['Appearance'])
                axis = self._axisDict[dic[i]['Axis']]
                obj = self.addInfiniteLineAnnotation(p, t, axis, appearance=appearance)
                i += 1

    # def removeAnnotation(self, annot):
    #    pass

    # def getAnnotations(self, type="all"):
    #    pass

    def _addLineAnnotation(self, pos, axis):
        warnings.warn(str(type(self)) + " does not implement _addLineAnnotation(pos, axis) method.", NotImplementedWarning)

    def _addInfiniteLineAnnotation(self, pos, axis):
        warnings.warn(str(type(self)) + " does not implement _addInfiniteLineAnnotation(pos, axis) method.", NotImplementedWarning)


class AnnotatableCanvasBase(object):
    def __init__(self):
        self._list = {}
        self._id_start = {}
        self._changed = {}
        self._id_seed = 10000

    def _setZOrder(self, obj, z):
        raise NotImplementedError()

    def _registerType(self, type):
        self._list[type] = []
        self._changed[type] = []
        self._id_start[type] = self._id_seed
        self._id_seed += 300

    def hasAnnotType(self, type):
        return type in self._list

    @saveCanvas
    def addAnnotation(self, type, name, obj, appearance=None, id=None):
        if id is None:
            ids = self._id_start[type] + len(self._list[type])
        else:
            ids = id
        self._addObject(obj)
        self._setZOrder(obj, ids)
        if appearance is None:
            self._list[type].insert(ids - self._id_start[type], AnnotationData(name, obj, ids, {}))
        else:
            self._list[type].insert(ids - self._id_start[type], AnnotationData(name, obj, ids, appearance))
        self._emitAnnotationChanged(type)
        return ids

    @saveCanvas
    def removeAnnotation(self, indexes, type='all'):
        for key, value in self._list.items():
            if type == key or type == "all":
                for i in indexes:
                    for d in value:
                        if i == d.id:
                            self._removeObject(d.obj)
                            self._list[type].remove(d)
            self._reorderAnnotation(type)
            self._emitAnnotationChanged(type)

    @saveCanvas
    def clearAnnotations(self, type='all'):
        list = self.getAnnotations(type)
        self.removeAnnotation([l.id for l in list], type)

    def _reorderAnnotation(self, type='text'):
        if type == "all":
            keys = self._list.keys()
        else:
            keys = [type]
        for k in keys:
            n = 0
            for d in self._list[k]:
                d.id = self._id_start[k] + n
                self._setZOrder(d.obj, d.id)
                n += 1

    def getAnnotations(self, type='all', indexes=None):
        if indexes is None:
            if type == 'all':
                res = []
                for v in self._list.values():
                    res.extend(v)
                return res
            return self._list[type]
        else:
            res = []
            if hasattr(indexes, "__iter__"):
                list = indexes
            else:
                list = [indexes]
            for i in list:
                for d in self.getAnnotations(type):
                    if i == d.id:
                        res.append(d)
            return res

    def getAnnotationFromIndexes(self, indexes=None, type='all'):
        return self.getAnnotations(type, indexes)

    def addAnnotationChangeListener(self, listener, type='text'):
        self._changed[type].append(weakref.ref(listener))

    def _emitAnnotationChanged(self, type='text'):
        if type == "all":
            keys = self._list.keys()
        else:
            keys = [type]
        for k in keys:
            for l in self._changed[k]:
                if l() is None:
                    self._changed[k].remove(l)
                else:
                    l().OnAnnotationChanged()

    def loadAnnotAppearance(self):
        pass

    def saveAnnotAppearance(self):
        pass
    # methods to be implemented

    def _addObject(self, obj, id):
        raise NotImplementedError()

    def _removeObject(self, obj):
        raise NotImplementedError()

    def _getAnnotAxis(self, obj):
        raise NotImplementedError()


class AnnotationEditableCanvasBase(AnnotatableCanvasBase):
    def __init__(self):
        super().__init__()
        self._edited = {}

    def _registerType(self, type):
        super()._registerType(type)
        self._edited[type] = []

    def _emitAnnotationEdited(self, type='text'):
        for l in self._edited[type]:
            if l() is None:
                self._edited[type].remove(l)
            else:
                l().OnAnnotationEdited()

    def addAnnotationEditedListener(self, listener, type='text'):
        self._edited[type].append(weakref.ref(listener))


class AnnotationSelectableCanvasBase(AnnotationEditableCanvasBase):
    def __init__(self):
        super().__init__()
        self._sel = {}
        self._selected = {}

    def _registerType(self, type):
        super()._registerType(type)
        self._sel[type] = []
        self._selected[type] = []

    def getSelectedAnnotations(self, type='text'):
        return self._sel[type]

    def setSelectedAnnotations(self, indexes, type='text'):
        if hasattr(indexes, '__iter__'):
            self._sel[type] = indexes
        else:
            self._sel[type] = [indexes]
        self._emitAnnotationSelected()

    def addAnnotationSelectedListener(self, listener, type='text'):
        self._selected[type].append(weakref.ref(listener))

    def _emitAnnotationSelected(self, type='text'):
        for l in self._selected[type]:
            if l() is None:
                self._selected[type].remove(l)
            else:
                l().OnAnnotationSelected()


class AnnotationOrderMovableCanvasBase(AnnotationSelectableCanvasBase):
    def _findIndex(self, id, type='text'):
        res = -1
        for d in self._list[type]:
            if d.id == id:
                res = self._list[type].index(d)
        return res

    @saveCanvas
    def moveAnnotation(self, list, target=None, type='text'):
        tar = eval(str(target))
        for l in list:
            n = self._findIndex(l)
            item_n = self._list[type][n]
            self._list[type].remove(item_n)
            if tar is not None:
                self._list[type].insert(self._findIndex(tar) + 1, item_n)
            else:
                self._list[type].insert(0, item_n)
        self._reorderAnnotation()


class AnnotationHidableCanvasBase(AnnotationOrderMovableCanvasBase):
    def saveAnnotAppearance(self):
        super().saveAnnotAppearance()
        data = self.getAnnotations()
        for d in data:
            d.appearance['Visible'] = self._isVisible(d.obj)

    def loadAnnotAppearance(self):
        super().loadAnnotAppearance()
        data = self.getAnnotations()
        for d in data:
            if 'Visible' in d.appearance:
                self._setVisible(d.obj, d.appearance['Visible'])

    @saveCanvas
    def hideAnnotation(self, indexes, type='text'):
        dat = self.getAnnotationFromIndexes(indexes, type=type)
        for d in dat:
            self._setVisible(d.obj, False)

    @saveCanvas
    def showAnnotation(self, indexes, type='text'):
        dat = self.getAnnotationFromIndexes(indexes, type=type)
        for d in dat:
            self._setVisible(d.obj, True)


class AnnotationCallbackCanvasBase(AnnotationHidableCanvasBase):
    def addCallback(self, indexes, callback):
        list = self.getAnnotations("all", indexes)
        for l in list:
            self._addAnnotCallback(l.obj, callback)

    def _addAnnotCallback(self, obj, callback):
        raise NotImplementedError()
