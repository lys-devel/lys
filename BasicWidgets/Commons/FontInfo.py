import matplotlib as mpl
import matplotlib.font_manager as fm

class FontInfo(object):
    _fonts=None
    def __init__(self,family,size=10,color='black'):
        self.family=str(family)
        self.size=size
        self.color=color
    def ToDict(self):
        dic={}
        dic['family']=self.family
        dic['size']=self.size
        dic['color']=self.color
        return dic
    @classmethod
    def FromDict(cls,dic):
        return FontInfo(dic['family'],dic['size'],dic['color'])
    @classmethod
    def loadFonts(cls):
        if cls._fonts is not None:
            return
        fonts = fm.findSystemFonts()
        cls._fonts=[]
        for f in fonts:
            n=fm.FontProperties(fname=f).get_name()
            if not n in cls._fonts:
                cls._fonts.append(n)
            cls._fonts=sorted(cls._fonts)
    @classmethod
    def defaultFont(cls):
        return FontInfo(fm.FontProperties(family=mpl.rcParams['font.family']).get_name())
