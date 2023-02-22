import warnings
import matplotlib as mpl
import matplotlib.font_manager as fm


class FontInfo(object):
    default = "Arial"
    _fonts = {}

    def __init__(self, fname, size=10, color="black"):
        if fname not in FontInfo.fonts():
            warnings.warn("Font [" + fname + "] not found. Use default font.")
            fname = FontInfo.defaultFont()
        self.fontName = fname
        self.size = size
        self.color = color

    def toDict(self):
        return {"fname": self.fontName, "size": self.size, "color": self.color}

    @staticmethod
    def fromDict(d):
        # for backward compability
        if "family" in d:
            d["fname"] = d["family"]
        return FontInfo(d["fname"], d["size"], d["color"])

    @classmethod
    def _loadFonts(cls):
        fonts = fm.findSystemFonts()
        for f in fonts:
            try:
                p = fm.FontProperties(fname=f)
                n = p.get_name()
                if n not in cls._fonts:
                    cls._fonts[n] = p
            except Exception:
                pass

    @classmethod
    def fonts(cls):
        return sorted(cls._fonts.keys())

    @classmethod
    def getFontProperty(cls, fname):
        prop = fm.FontProperties(family=fname)
        if prop.get_name() != fname:
            return cls._fonts[fname]
        return prop

    @classmethod
    def defaultFont(cls):
        if cls.default in cls.fonts():
            return cls.default
        return fm.FontProperties(family=mpl.rcParams['font.family']).get_name()


FontInfo._loadFonts()
