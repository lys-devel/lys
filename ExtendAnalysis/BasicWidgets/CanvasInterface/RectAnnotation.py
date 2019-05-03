from .CanvasBase import *
from .SaveCanvas import *

class RectAnnotationCanvasBase(object):
    def __init__(self):
        self._registerType('rect')
    @saveCanvas
    def addRect(self,pos,size,axis=Axis.BottomLeft,appearance=None,id=None):
        roi=self._makeRectAnnot(pos,size,axis)
        return self.addAnnotation('rect','rect',roi,appearance=appearance,id=id)
    def _makeRectAnnot(self,pos,axis):
        raise NotImplementedError()
    def _getRectPosition(self,obj):
        raise NotImplementedError()
    def _getRectSize(self,obj):
        raise NotImplementedError()
    def SaveAsDictionary(self,dictionary,path):
        #super().SaveAsDictionary(dictionary,path)
        i=0
        dic={}
        self.saveAnnotAppearance()
        for data in self._list['rect']:
            dic[i]={}
            dic[i]['Position']=self._getRectPosition(data.obj)
            dic[i]['Size']=self._getRectSize(data.obj)
            dic[i]['Axis'] = int(self._getAnnotAxis(data.obj))
            dic[i]['Appearance']=str(data.appearance)
            i+=1
        dictionary['annot_rect']=dic
    def LoadFromDictionary(self,dictionary,path):
        #super().LoadFromDictionary(dictionary,path)
        if 'annot_rect' in dictionary:
            dic=dictionary['annot_rect']
            i=0
            while i in dic:
                p=dic[i]['Position']
                s=dic[i]['Size']
                appearance=eval(dic[i]['Appearance'])
                axis = Axis(dic[i]['Axis'])
                self.addRect(p,s,axis,appearance=appearance)
                i+=1
        self.loadAnnotAppearance()
