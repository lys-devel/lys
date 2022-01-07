import matplotlib as mpl
import matplotlib.font_manager as fm

from LysQt.QtCore import pyqtSignal
from .CanvasBase import CanvasPart, saveCanvas


class FontInfo(object):
    _fonts = None

    def __init__(self, family, size=10, color='black'):
        self.family = str(family)
        self.size = size
        self.color = color

    def ToDict(self):
        dic = {}
        dic['family'] = self.family
        dic['size'] = self.size
        dic['color'] = self.color
        return dic

    @classmethod
    def FromDict(cls, dic):
        return FontInfo(dic['family'], dic['size'], dic['color'])

    @classmethod
    def loadFonts(cls):
        if cls._fonts is not None:
            return
        fonts = fm.findSystemFonts()
        cls._fonts = []
        for f in fonts:
            try:
                n = fm.FontProperties(fname=f).get_name()
                if not n in cls._fonts:
                    cls._fonts.append(n)
                cls._fonts = sorted(cls._fonts)
            except:
                pass

    @classmethod
    def fonts(cls):
        if cls._fonts is None:
            fonts = fm.findSystemFonts()
            cls._fonts = []
            for f in fonts:
                try:
                    n = fm.FontProperties(fname=f).get_name()
                    if not n in cls._fonts:
                        cls._fonts.append(n)
                except Exception:
                    pass
        cls._fonts = sorted(cls._fonts)
        return cls._fonts

    @classmethod
    def defaultFamily(cls):
        return fm.FontProperties(family=mpl.rcParams['font.family']).get_name()

    @classmethod
    def defaultFont(cls):
        return FontInfo(fm.FontProperties(family=mpl.rcParams['font.family']).get_name())


class CanvasFont(CanvasPart):
    """Font manager class for canvas."""
    fontChanged = pyqtSignal(str)
    """Emitted when fonts are changed."""

    def __init__(self, canvas):
        super().__init__(canvas)
        self.__font = {}
        self.__def = {}
        self.__font['Default'] = FontInfo.defaultFont()
        self.__def['Default'] = False
        canvas.saveCanvas.connect(self._save)
        canvas.loadCanvas.connect(self._load)

    def _save(self, dictionary):
        dic = {}
        dic_def = {}
        for name in self.__font.keys():
            dic[name] = self.__font[name].ToDict()
            dic_def[name] = self.__def[name]
        dictionary['Font'] = dic
        dictionary['Font_def'] = dic_def

    def _load(self, dictionary):
        if 'Font' in dictionary:
            dic = dictionary['Font']
            dic_def = dictionary['Font_def']
            for d in dic.keys():
                self.__font[d] = FontInfo.FromDict(dic[d])
                self.__def[d] = dic_def[d]

    def getCanvasFont(self, name='Default'):
        if name in self.__font:
            if not self.__def[name]:
                return self.__font[name]
        return self.__font['Default']

    @saveCanvas
    def setCanvasFont(self, font, name='Default'):
        self.__font[name] = font
        self.fontChanged.emit(name)

    @saveCanvas
    def setCanvasFontDefault(self, b, name):
        self.__def[name] = b
        self.fontChanged.emit(name)

    def getCanvasFontDefault(self, name):
        if name in self.__font:
            if not self.__def[name]:
                return False
        return True
