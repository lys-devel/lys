from .CanvasBase import *


class LineColorAdjustableCanvasBase(OffsetAdjustableCanvasBase):
    def saveAppearance(self):
        super().saveAppearance()
        data = self.getLines()
        for d in data:
            d.appearance['LineColor'] = self._getDataColor(d.obj)

    @saveCanvas
    def setDataColor(self, color, indexes):
        data = self.getDataFromIndexes(1, indexes)
        for d in data:
            self._setDataColor(d.obj, color)

    def getDataColor(self, indexes):
        res = []
        data = self.getDataFromIndexes(1, indexes)
        for d in data:
            res.append(self._getDataColor(d.obj))
        return res

    def loadAppearance(self):
        super().loadAppearance()
        data = self.getLines()
        for d in data:
            if 'LineColor' in d.appearance:
                self._setDataColor(d.obj, d.appearance['LineColor'])

    def _setDataColor(self, obj, color):
        raise NotImplementedError()

    def _getDataColor(self, obj):
        raise NotImplementedError()


class LineStyleAdjustableCanvasBase(LineColorAdjustableCanvasBase):
    def saveAppearance(self):
        super().saveAppearance()
        data = self.getLines()
        for d in data:
            d.appearance['LineStyle'] = self._getLineDataStyle(d.obj)
            d.appearance['LineWidth'] = self._getLineDataWidth(d.obj)

    @saveCanvas
    def setLineStyle(self, style, indexes):
        data = self.getDataFromIndexes(1, indexes)
        for d in data:
            self._setLineDataStyle(d.obj, style)
            d.appearance['OldLineStyle'] = self._getLineDataStyle(d.obj)

    def getLineStyle(self, indexes):
        res = []
        data = self.getDataFromIndexes(1, indexes)
        for d in data:
            res.append(self._getLineDataStyle(d.obj))
        return res

    @saveCanvas
    def setDataWidth(self, width, indexes):
        data = self.getDataFromIndexes(1, indexes)
        for d in data:
            self._setLineDataWidth(d.obj, width)

    def getLineWidth(self, indexes):
        res = []
        data = self.getDataFromIndexes(1, indexes)
        for d in data:
            res.append(self._getLineDataWidth(d.obj))
        return res

    def loadAppearance(self):
        super().loadAppearance()
        data = self.getLines()
        for d in data:
            if 'LineStyle' in d.appearance:
                self._setLineDataStyle(d.obj, d.appearance['LineStyle'])
            if 'LineWidth' in d.appearance:
                self._setLineDataWidth(d.obj, d.appearance['LineWidth'])

    def _getLineDataStyle(self, obj):
        raise NotImplementedError()

    def _setLineDataStyle(self, obj, style):
        raise NotImplementedError()

    def _getLineDataWidth(self, obj):
        raise NotImplementedError()

    def _setLineDataWidth(self, obj, width):
        raise NotImplementedError()


class MarkerStyleAdjustableCanvasBase(LineStyleAdjustableCanvasBase):
    def saveAppearance(self):
        super().saveAppearance()
        data = self.getLines()
        for d in data:
            d.appearance['Marker'] = self._getMarker(d.obj)
            d.appearance['MarkerSize'] = self._getMarkerSize(d.obj)
            d.appearance['MarkerThick'] = self._getMarkerThick(d.obj)
            d.appearance['MarkerFilling'] = self._getMarkerFilling(d.obj)

    @saveCanvas
    def setMarker(self, marker, indexes):
        data = self.getDataFromIndexes(1, indexes)
        for d in data:
            self._setMarker(d.obj, marker)
            d.appearance['OldMarker'] = self._getMarker(d.obj)

    def getMarker(self, indexes):
        return [self._getMarker(d.obj) for d in self.getDataFromIndexes(1, indexes)]

    @saveCanvas
    def setMarkerSize(self, size, indexes):
        data = self.getDataFromIndexes(1, indexes)
        for d in data:
            self._setMarkerSize(d.obj, size)

    def getMarkerSize(self, indexes):
        return [self._getMarkerSize(d.obj) for d in self.getDataFromIndexes(1, indexes)]

    @saveCanvas
    def setMarkerThick(self, size, indexes):
        data = self.getDataFromIndexes(1, indexes)
        for d in data:
            self._setMarkerThick(d.obj, size)

    def getMarkerThick(self, indexes):
        return [self._getMarkerThick(d.obj) for d in self.getDataFromIndexes(1, indexes)]

    @saveCanvas
    def setMarkerFilling(self, type, indexes):
        for d in self.getDataFromIndexes(1, indexes):
            self._setMarkerFilling(d.obj, type)

    def getMarkerFilling(self, indexes):
        return [self._getMarkerFilling(d.obj) for d in self.getDataFromIndexes(1, indexes)]

    def loadAppearance(self):
        super().loadAppearance()
        data = self.getLines()
        for d in data:
            if 'Marker' in d.appearance:
                self._setMarker(d.obj, d.appearance['Marker'])
            if 'MarkerSize' in d.appearance:
                self._setMarkerSize(d.obj, d.appearance['MarkerSize'])
            if 'MarkerThick' in d.appearance:
                self._setMarkerThick(d.obj, d.appearance['MarkerThick'])
            if 'MarkerFilling' in d.appearance:
                self._setMarkerFilling(d.obj, d.appearance['MarkerFilling'])

    def _getMarker(self, obj):
        raise NotImplementedError()

    def _getMarkerSize(self, obj):
        raise NotImplementedError()

    def _getMarkerThick(self, obj):
        raise NotImplementedError()

    def _getMarkerFilling(self, obj):
        raise NotImplementedError()

    def _setMarker(self, obj, marker):
        raise NotImplementedError()

    def _setMarkerSize(self, obj, size):
        raise NotImplementedError()

    def _setMarkerThick(self, obj, thick):
        raise NotImplementedError()

    def _setMarkerFilling(self, obj, filling):
        raise NotImplementedError()

    def getMarkerList(self):
        raise NotImplementedError()

    def getMarkerFillingList(self):
        raise NotImplementedError()
