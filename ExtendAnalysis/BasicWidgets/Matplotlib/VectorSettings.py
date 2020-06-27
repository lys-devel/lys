from .RGBSettings import *


class VectorScalableCanvas(RGBSettingCanvas):
    @saveCanvas
    def setVectorPivot(self, indexes, pivot):
        data = self.getDataFromIndexes("vector", indexes)
        for d in data:
            self._setVectorPivot(d.obj, pivot)

    def getVectorPivot(self, indexes):
        data = self.getDataFromIndexes("vector", indexes)
        return [self._getVectorPivot(d.obj) for d in data]

    def _setVectorPivot(self, obj, pivot):
        obj.pivot = pivot

    def _getVectorPivot(self, obj):
        return obj.pivot

    @saveCanvas
    def setVectorScale(self, indexes, scale):
        data = self.getDataFromIndexes("vector", indexes)
        for d in data:
            self._setVectorScale(d.obj, scale)

    def getVectorScale(self, indexes):
        data = self.getDataFromIndexes("vector", indexes)
        return [self._getVectorScale(d.obj) for d in data]

    def _setVectorScale(self, obj, scale):
        if scale is not 0:
            obj.scale = scale
        else:
            obj.scale = None

    def _getVectorScale(self, obj):
        return obj.scale

    @saveCanvas
    def setVectorWidth(self, indexes, width):
        data = self.getDataFromIndexes("vector", indexes)
        for d in data:
            self._setVectorWidth(d.obj, width)

    def getVectorWidth(self, indexes):
        data = self.getDataFromIndexes("vector", indexes)
        return [self._getVectorWidth(d.obj) for d in data]

    def _setVectorWidth(self, obj, width):
        if width is not 0:
            obj.width = width
        else:
            obj.width = None

    def _getVectorWidth(self, obj):
        return obj.width

    @saveCanvas
    def setVectorColor(self, indexes, color, type="all"):
        data = self.getDataFromIndexes("vector", indexes)
        for d in data:
            self._setVectorColor(d.obj, color, type)

    def getVectorColor(self, indexes, type="face"):
        data = self.getDataFromIndexes("vector", indexes)
        return [self._getVectorColor(d.obj, type) for d in data]

    def _setVectorColor(self, obj, color, type):
        if type == "all":
            obj.set_color(color)
        if type == "face":
            obj.set_facecolor(color)
        if type == "edge":
            obj.set_edgecolor(color)

    def _getVectorColor(self, obj, type):
        if type == "face":
            return obj.get_facecolor()[0].tolist()
        if type == "edge":
            list = obj.get_edgecolor()
            if len(list) == 0:
                return self._getVectorColor(obj, "face")
            else:
                return list[0].tolist()

    def saveAppearance(self):
        super().saveAppearance()
        data = self.getVectorFields()
        for d in data:
            d.appearance['VectorScale'] = self._getVectorScale(d.obj)
            d.appearance['VectorWidth'] = self._getVectorWidth(d.obj)
            d.appearance['VectorColor'] = self._getVectorColor(d.obj, "face")
            d.appearance['VectorEdgeColor'] = self._getVectorColor(d.obj, "edge")
            d.appearance['VectorPivot'] = self._getVectorPivot(d.obj)

    def loadAppearance(self):
        super().loadAppearance()
        data = self.getVectorFields()
        for d in data:
            if 'VectorColor' in d.appearance:
                self._setVectorColor(d.obj, d.appearance['VectorColor'], "face")
            if 'VectorEdgeColor' in d.appearance:
                self._setVectorColor(d.obj, d.appearance['VectorEdgeColor'], "edge")
            if 'VectorScale' in d.appearance:
                self._setVectorScale(d.obj, d.appearance['VectorScale'])
            if 'VectorWidth' in d.appearance:
                self._setVectorWidth(d.obj, d.appearance['VectorWidth'])
            if 'VectorPivot' in d.appearance:
                self._setVectorPivot(d.obj, d.appearance['VectorPivot'])


class VectorSettingCanvas(VectorScalableCanvas):
    pass
