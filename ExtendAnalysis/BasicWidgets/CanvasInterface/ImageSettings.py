import sys
from .LineSettings import *


class ImageColorAdjustableCanvasBase(MarkerStyleAdjustableCanvasBase):
    @saveCanvas
    def setColormap(self, cmap, indexes):
        data = self.getDataFromIndexes(2, indexes)
        for d in data:
            self._setColormap(d, cmap)

    def getColormap(self, indexes):
        res = []
        data = self.getDataFromIndexes(2, indexes)
        for d in data:
            res.append(self._getColormap(d))
        return res

    def getColorRange(self, indexes):
        res = []
        data = self.getDataFromIndexes(2, indexes)
        for d in data:
            res.append(self._getColorRange(d))
        return res

    @saveCanvas
    def setColorRange(self, indexes, min, max, log=False):
        ma, mi, lo = max, min, log
        if max < min:
            ma = min
        if log and (min <= 0 or max <= 0):
            print('[ImageSetting] Values must all be positive. Log is disabled.', file=sys.stderr)
            lo = False
        data = self.getDataFromIndexes(2, indexes)
        for d in data:
            self._setColorRange(d, mi, ma, lo)

    def isLog(self, indexes):
        res = []
        data = self.getDataFromIndexes(2, indexes)
        for d in data:
            res.append(self._isLog(d))
        return res

    def getAutoColorRange(self, indexes):
        data = self.getDataFromIndexes(2, indexes)
        res = []
        for d in data:
            dat = np.nan_to_num(d.wave.data)
            ma, mi = np.percentile(dat, [75, 25])
            dat = np.clip(dat, mi, ma)
            var = np.sqrt(dat.var()) * 3
            if var == 0:
                var = 1
            mean = dat.mean()
            res.append((mean, var))
        return res

    @saveCanvas
    def autoColorRange(self, indexes):
        ranges = self.getAutoColorRange(indexes)
        data = self.getDataFromIndexes(2, indexes)
        for d, (i, (m, v)) in zip(data, zip(indexes, ranges)):
            self.setColorRange(i, m - v, m + v, log=self._isLog(d))

    def getOpacity(self, indexes):
        data = self.getDataFromIndexes(2, indexes)
        return [self._getOpacity(d) for d in data]

    @saveCanvas
    def setOpacity(self, indexes, value):
        data = self.getDataFromIndexes(2, indexes)
        for d in data:
            self._setOpacity(d, value)

    def saveAppearance(self):
        super().saveAppearance()
        for d in self.getImages():
            d.appearance['Colormap'] = self._getColormap(d)
            d.appearance['Range'] = self._getColorRange(d)
            d.appearance['Log'] = self._isLog(d)
            d.appearance['Opacity'] = self._getOpacity(d)

    def loadAppearance(self):
        super().loadAppearance()
        for d in self.getImages():
            if 'Colormap' in d.appearance:
                self._setColormap(d, d.appearance['Colormap'])
            if 'Range' in d.appearance:
                log = d.appearance.get('Log', False)
                min, max = d.appearance['Range']
                self._setColorRange(d, min, max, log)
            if 'Opacity' in d.appearance:
                self._setOpacity(d, d.appearance['Opacity'])
