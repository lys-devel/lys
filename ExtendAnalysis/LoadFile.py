"""
All interfaces to this module is written in :mod:`.functions` and :mod:`.plugin` modules
"""

import os


def _load(name, *args, **kwargs):
    """see lys.functions.load"""
    if os.path.isfile(name):
        path, ext = os.path.splitext(name)
        res = _dic[ext](os.path.abspath(name), *args, **kwargs)
        if hasattr(res, "setLoadFile"):
            res.setLoadFile(name)
        return res


def __loadNpz(name):
    """load numpy npz file"""
    from . import Wave
    nam, ext = os.path.splitext(os.path.basename(name))
    return Wave(name)


def __loadDic(name):
    """load Setting Dict"""
    from . import SettingDict
    nam, ext = os.path.splitext(os.path.basename(name))
    return SettingDict(name)


def __loadGraph(name):
    """load lys Graph"""
    from . import Graph
    nam, ext = os.path.splitext(os.path.basename(name))
    return Graph(name)


def __loadImage(name):
    """load png, tiff, jpg as Wave"""
    from . import Wave
    from PIL import Image
    im = Image.open(name)
    return Wave(im)


def _addFileLoader(type, func):
    """see lys.plugin.registerFileLoader"""
    _dic[type] = func


def _getExtentions():
    """see lys.plugin.loadableFiles"""
    return _dic.keys()


_dic = dict(zip(['.npz', '.dic', '.grf', '.tif', '.jpg', '.png'], [__loadNpz, __loadDic, __loadGraph, __loadImage, __loadImage, __loadImage]))


"""
def getShape(name, *args, **kwargs):
    path, ext = os.path.splitext(name)
    if ext == ".npz":
        try:
            with zipfile.ZipFile(name) as archive:
                name = "data.npy"
                npy = archive.open(name)
                version = np.lib.format.read_magic(npy)
                shape, fortran, dtype = np.lib.format._read_array_header(npy, version)
                return shape
        except:
            pass
    f = load(name, *args, **kwargs)
    return f.data.shape


def getDtype(name, *args, **kwargs):
    path, ext = os.path.splitext(name)
    if ext == ".npz":
        try:
            with zipfile.ZipFile(name) as archive:
                name = "data.npy"
                npy = archive.open(name)
                version = np.lib.format.read_magic(npy)
                shape, fortran, dtype = np.lib.format._read_array_header(npy, version)
                return dtype
        except:
            pass
    f = load(name, *args, **kwargs)
    return f.data.dtype


def getAxes(name, *args, **kwargs):
    path, ext = os.path.splitext(name)
    if ext == ".npz":
        try:
            tmp = np.load(name, allow_pickle=True)
            return tmp["axes"].to_list()
        except:
            pass
    f = load(name, *args, **kwargs)
    return f.axes


def getNotes(name, *args, **kwargs):
    path, ext = os.path.splitext(name)
    if ext == ".npz":
        try:
            tmp = np.load(name, allow_pickle=True)
            return tmp["note"].item()
        except:
            pass
    f = load(name, *args, **kwargs)
    return f.note

"""
