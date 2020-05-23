import weakref

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .CanvasBase import *
from .SaveCanvas import *


class AnnotationData(object):
    def __init__(self, name, obj, idn, appearance):
        self.name = name
        self.obj = obj
        self.id = idn
        self.appearance = appearance
        self.axes = Axis.BottomLeft


class AnnotatableCanvasBase(object):
    def __init__(self):
        self._list = {}
        self._id_start = {}
        self._changed = {}
        self._id_seed = 10000

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


class AnnotLineColorAdjustableCanvas(AnnotationHidableCanvasBase):
    def saveAnnotAppearance(self):
        super().saveAnnotAppearance()
        data = self.getAnnotations()
        for d in data:
            d.appearance['LineColor'] = self._getLineColor(d.obj)

    def loadAnnotAppearance(self):
        super().loadAnnotAppearance()
        data = self.getAnnotations()
        for d in data:
            if 'LineColor' in d.appearance:
                self.setAnnotLineColor(d.appearance['LineColor'], d.id)

    @saveCanvas
    def setAnnotLineColor(self, color, indexes):
        data = self.getAnnotationFromIndexes(indexes)
        for d in data:
            self._setLineColor(d.obj, color)

    def getAnnotLineColor(self, indexes):
        data = self.getAnnotationFromIndexes(indexes)
        return [self._getLineColor(d.obj) for d in data]

    def _getLineColor(self, obj):
        raise NotImplementedError()

    def _setLineColor(self, obj, color):
        raise NotImplementedError()


class AnnotLineStyleAdjustableCanvas(AnnotLineColorAdjustableCanvas):
    @saveCanvas
    def setAnnotLineStyle(self, style, indexes):
        data = self.getAnnotationFromIndexes(indexes)
        for d in data:
            self._setLineStyle(d.obj, style)
            d.appearance['OldLineStyle'] = self._getLineStyle(d.obj)

    def getAnnotLineStyle(self, indexes):
        data = self.getAnnotationFromIndexes(indexes)
        return [self._getLineStyle(d.obj) for d in data]

    @saveCanvas
    def setAnnotLineWidth(self, width, indexes):
        data = self.getAnnotationFromIndexes(indexes)
        for d in data:
            self._setLineWidth(d.obj, width)

    def getAnnotLineWidth(self, indexes):
        data = self.getAnnotationFromIndexes(indexes)
        return [self._getLineWidth(d.obj) for d in data]

    def saveAnnotAppearance(self):
        super().saveAnnotAppearance()
        data = self.getAnnotations()
        for d in data:
            d.appearance['LineStyle'] = self._getLineStyle(d.obj)
            d.appearance['LineWidth'] = self._getLineWidth(d.obj)

    def loadAnnotAppearance(self):
        super().loadAnnotAppearance()
        data = self.getAnnotations()
        for d in data:
            if 'LineStyle' in d.appearance:
                self.setAnnotLineStyle(d.appearance['LineStyle'], d.id)
            if 'LineWidth' in d.appearance:
                self.setAnnotLineWidth(d.appearance['LineWidth'], d.id)

    def _getLineStyle(self, obj):
        pass

    def _setLineStyle(self, obj, style):
        pass

    def _getLineWidth(self, obj):
        pass

    def _setLineWidth(self, obj, width):
        pass


class AnnotationCallbackCanvasBase(AnnotLineStyleAdjustableCanvas):
    def addCallback(self, indexes, callback):
        list = self.getAnnotations("all", indexes)
        for l in list:
            self._addAnnotCallback(l.obj, callback)

    def _addAnnotCallback(self, obj, callback):
        raise NotImplementedError()
