from .CanvasBase import *
from .SaveCanvas import *

class TextAnnotationCanvasBase(object):
    def __init__(self):
        self._registerType('text')
    @saveCanvas
    def addText(self,text,axis=Axis.BottomLeft,appearance=None,id=None, x=0.5, y=0.5, box=dict(boxstyle='round', fc='w'), size=10, picker=True):
        obj=self._makeObject(text,axis,appearance,id, x, y, box, size, picker)
        return self.addAnnotation('text',text,obj,appearance,id)
    @saveCanvas
    def setAnnotationText(self,indexes,txt):
        list=self.getAnnotationFromIndexes(indexes)
        for l in list:
            self._setText(l.obj,txt)
        self._emitAnnotationEdited()
    def getAnnotationText(self,indexes):
        list=self.getAnnotationFromIndexes(indexes)
        return [self._getText(l.obj) for l in list]
    def SaveAsDictionary(self,dictionary,path):
        #super().SaveAsDictionary(dictionary,path)
        dic={}
        self.saveAnnotAppearance()
        for i, data in enumerate(self._list['text']):
            dic[i]={}
            dic[i]['Text']=self._getText(data.obj)
            dic[i]['Appearance']=str(data.appearance)
            dic[i]['Axis']=int(self._getAnnotAxis(data.obj))
        dictionary['Textlist']=dic
    def LoadFromDictionary(self,dictionary,path):
        if 'Textlist' in dictionary:
            dic=dictionary['Textlist']
            i=0
            while i in dic:
                t=dic[i]['Text']
                appearance=eval(dic[i]['Appearance'])
                axis=Axis(dic[i]['Axis'])
                self.addText(t,axis,appearance=appearance)
                i+=1
    # methods to be implemented
    def _makeObject(self,text,axis,appearance,id, x, y, box, size, picker):
        raise NotImplementedError()
    def _setText(self,obj,txt):
        raise NotImplementedError()
    def _getText(self,obj):
        raise NotImplementedError()
