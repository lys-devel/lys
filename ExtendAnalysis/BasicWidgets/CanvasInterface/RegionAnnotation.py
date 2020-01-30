from .CanvasBase import *
from .SaveCanvas import *


class RegionAnnotationCanvasBase(object):
    def __init__(self):
        self._registerType('horizontal')
        self._registerType('vertical')

    @saveCanvas
    def addRegion(self, region=None, type='vertical', axis=Axis.BottomLeft, appearance=None, id=None):
        if region is None:
            if type == 'vertical':
                r = self.getAxisRange('Bottom')
            else:
                r = self.getAxisRange('Left')
            region = (np.min(r) + (np.max(r) - np.min(r)) * 4 / 10, np.min(r) + (np.max(r) - np.min(r)) * 6 / 10)
        roi = self._makeRegionAnnot(region, type, axis)
        return self.addAnnotation(type, type, roi, appearance=appearance, id=id)

    def _makeRegionAnnot(self, region, type, axis):
        raise NotImplementedError()

    def _getRegion(self, obj):
        raise NotImplementedError()

    def SaveAsDictionary(self, dictionary, path):
        # super().SaveAsDictionary(dictionary,path)
        i = 0
        dic = {}
        self.saveAnnotAppearance()
        for type in ['horizontal', 'vertical']:
            for data in self._list[type]:
                dic[i] = {}
                dic[i]['Position'] = self._getRegion(data.obj)
                dic[i]['Type'] = type
                dic[i]['Axis'] = int(self._getAnnotAxis(data.obj))
                dic[i]['Appearance'] = str(data.appearance)
                i += 1
        dictionary['annot_region'] = dic

    def LoadFromDictionary(self, dictionary, path):
        # super().LoadFromDictionary(dictionary,path)
        if 'annot_region' in dictionary:
            dic = dictionary['annot_region']
            i = 0
            while i in dic:
                p = dic[i]['Position']
                t = dic[i]['Type']
                appearance = eval(dic[i]['Appearance'])
                axis = Axis(dic[i]['Axis'])
                self.addRegion(p, t, axis, appearance=appearance)
                i += 1
        self.loadAnnotAppearance()
