from .CanvasBase import *
from .SaveCanvas import *

class LineAnnotationCanvasBase(object):
    def __init__(self):
        self._registerType('line')
    @saveCanvas
    def addLine(self,pos=None,axis=Axis.BottomLeft,appearance=None,id=None):
        line=self._makeLineAnnot(pos,axis)
        return self.addAnnotation('line','line',line,appearance=appearance,id=id)
    def SaveAsDictionary(self,dictionary,path):
        #super().SaveAsDictionary(dictionary,path)
        dic={}
        self.saveAnnotAppearance()
        for i, data in enumerate(self._list['line']):
            dic[i]={}
            pos=self._getLinePosition(data.obj)
            dic[i]['Position0']=list(pos[0])
            dic[i]['Position1']=list(pos[1])
            dic[i]['Appearance']=str(data.appearance)
            dic[i]['Axis']=int(self._getAnnotAxis(data.obj))
        dictionary['annot_lines']=dic
    def LoadFromDictionary(self,dictionary,path):
        #super().LoadFromDictionary(dictionary,path)
        if 'annot_lines' in dictionary:
            dic=dictionary['annot_lines']
            i=0
            while i in dic:
                p0=dic[i]['Position0']
                p1=dic[i]['Position1']
                p=[[p0[0],p1[0]],[p0[1],p1[1]]]
                appearance=eval(dic[i]['Appearance'])
                axis=Axis(dic[i]['Axis'])
                self.addLine(p,axis=axis,appearance=appearance)
                i+=1
        self.loadAnnotAppearance()
    def _makeLineAnnot(self,pos,axis):
        raise NotImplementedError()
    def _getLinePosition(self,obj):
        raise NotImplementedError()
