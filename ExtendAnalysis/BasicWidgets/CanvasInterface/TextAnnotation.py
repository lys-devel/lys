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
            axis = self._getAnnotAxis(data.obj)
            if axis == Axis.BottomLeft:
                axis=1
            if axis == Axis.TopLeft:
                axis=2
            if axis == Axis.BottomRight:
                axis=3
            if axis == Axis.TopRight:
                axis=4
            dic[i]['Axis']=axis
        dictionary['Textlist']=dic
    def LoadFromDictionary(self,dictionary,path):
        if 'Textlist' in dictionary:
            dic=dictionary['Textlist']
            i=0
            while i in dic:
                t=dic[i]['Text']
                appearance=eval(dic[i]['Appearance'])
                axis=dic[i]['Axis']
                if axis==1:
                    axis=Axis.BottomLeft
                if axis==2:
                    axis=Axis.TopLeft
                if axis==3:
                    axis=Axis.BottomRight
                if axis==4:
                    axis=Axis.TopRight
                self.addText(t,axis,appearance=appearance)
                i+=1
    # methods to be implemented
    def _makeObject(self,text,axis,appearance,id, x, y, box, size, picker):
        raise NotImplementedError()
    def _setText(self,obj,txt):
        raise NotImplementedError()
    def _getText(self,obj):
        raise NotImplementedError()
    def _getAnnotAxis(self,obj):
        raise NotImplementedError()
