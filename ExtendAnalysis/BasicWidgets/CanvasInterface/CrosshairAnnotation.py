from .CanvasBase import *
from .SaveCanvas import *


class CrosshairAnnotationCanvasBase(object):
    def __init__(self):
        self._registerType('cross')

    @saveCanvas
    def addCross(self, pos=None, axis=Axis.BottomLeft, appearance=None, id=None):
        if pos is None:
            rb = self.getAxisRange('Bottom')
            rl = self.getAxisRange('Left')
            pos = (np.min(rb) + (np.max(rb) - np.min(rb)) / 2, np.min(rl) + (np.max(rl) - np.min(rl)) / 2)
        roi = self._makeCrossAnnot(pos, axis)
        return self.addAnnotation('cross', 'cross', roi, appearance=appearance, id=id)

    def _makeCrossAnnot(self, region, type, axis):
        raise NotImplementedError()

    def _getPosition(self, obj):
        raise NotImplementedError()

    def SaveAsDictionary(self, dictionary, path):
        # super().SaveAsDictionary(dictionary,path)
        i = 0
        dic = {}
        self.saveAnnotAppearance()
        for data in self._list['cross']:
            dic[i] = {}
            dic[i]['Position'] = self._getPosition(data.obj)
            dic[i]['Axis'] = int(self._getAnnotAxis(data.obj))
            dic[i]['Appearance'] = str(data.appearance)
            i += 1
        dictionary['annot_cross'] = dic

    def LoadFromDictionary(self, dictionary, path):
        # super().LoadFromDictionary(dictionary,path)
        if 'annot_cross' in dictionary:
            dic = dictionary['annot_cross']
            i = 0
            while i in dic:
                p = dic[i]['Position']
                appearance = eval(dic[i]['Appearance'])
                axis = Axis(dic[i]['Axis'])
                self.addCross(p, t, axis, appearance=appearance)
                i += 1
        self.loadAnnotAppearance()
