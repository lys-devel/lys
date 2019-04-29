from .AxisSettings import *
from ExtendAnalysis.BasicWidgets.Commons.FontInfo import *
from .CanvasBase import saveCanvas

class FontSelectableCanvas(TickAdjustableCanvas):
    def __init__(self,dpi=100):
        super().__init__(dpi=dpi)
        self.__font={}
        self.__def={}
        self.__font['Default']=FontInfo.defaultFont()
        self.__def['Default']=False
        self.__listener=[]
    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        dic={}
        dic_def={}
        for name in self.__font.keys():
            dic[name]=self.__font[name].ToDict()
            dic_def[name]=self.__def[name]
        dictionary['Font']=dic
        dictionary['Font_def']=dic_def
    def LoadFromDictionary(self,dictionary,path):
        super().LoadFromDictionary(dictionary,path)
        if 'Font' in dictionary:
            dic=dictionary['Font']
            dic_def=dictionary['Font_def']
            for d in dic.keys():
                self.__font[d]=FontInfo.FromDict(dic[d])
                self.__def[d]=dic_def[d]
    def addFontChangeListener(self,listener):
        self.__listener.append(weakref.ref(listener))
    def _emit(self,name):
        for l in self.__listener:
            if l() is None:
                self.__listener.remove(l)
            else:
                l().OnFontChanged(name)
    @saveCanvas
    def addFont(self,name):
        if not name in self.__font:
            self.__font[name]=FontInfo(self.__font['Default'].family)
            self.__def[name]=True
    def getFont(self,name='Default'):
        if name in self.__font:
            if not self.__def[name]:
                return self.__font[name]
        return self.__font['Default']
    @saveCanvas
    def setFont(self,font,name='Default'):
        self.__font[name]=font
        self._emit(name)
    @saveCanvas
    def setFontDefault(self,b,name):
        self.__def[name]=b
        self._emit(name)
    def getFontDefault(self,name):
        if name in self.__font:
            if not self.__def[name]:
                return False
        return True
