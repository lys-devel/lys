import os
import sys
import zipfile
import numpy as np
from .ExtendType import *
from .BasicWidgets.GraphWindow import Graph
from .FileLoader import *


def load(name, load=True, disconnect=False):
    if os.path.isdir(name):
        os.makedirs(os.getcwd() + '/' + os.path.basename(name), exist_ok=True)
        __loadFolder(name, os.getcwd() + '/' + os.path.basename(name))
    elif os.path.isfile(name):
        path, ext = os.path.splitext(name)
        res = dic[ext](os.path.abspath(name))
        if hasattr(res, "setLoadFile"):
            res.setLoadFile(name)
        if disconnect:
            res.Disconnect()
        if load:
            return res


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


def save(name, nameAs):
    data = load(name)
    data.Save(nameAs)


def __loadFolder(name, path):
    files = os.listdir(name)
    for file in files:
        if os.path.isdir(name + '/' + file):
            os.makedirs(path + '/' + file, exist_ok=True)
            __loadFolder(name + '/' + file, path + '/' + file)
        elif os.path.isfile(name + '/' + file):
            nam, ext = os.path.splitext(file)
            data = load(os.path.abspath(name + '/' + file))
            if isinstance(data, Wave):
                data.Save(path + '/' + nam + '.npz')
            if isinstance(data, Graph):
                data.Save(path + '/' + nam + '.grf')
            if isinstance(data, String):
                data.Save(path + '/' + nam + '.str')
            if isinstance(data, Variable):
                data.Save(path + '/' + nam + '.val')
            if isinstance(data, Dict):
                data.Save(path + '/' + nam + '.dic')
            if isinstance(data, List):
                data.Save(path + '/' + nam + '.lst')


def __loadNpz(name):
    nam, ext = os.path.splitext(os.path.basename(name))
    return Wave(name)


def __loadStr(name):
    nam, ext = os.path.splitext(os.path.basename(name))
    return String(name)


def __loadVal(name):
    nam, ext = os.path.splitext(os.path.basename(name))
    return Variable(name)


def __loadDic(name):
    nam, ext = os.path.splitext(os.path.basename(name))
    return Dict(name)


def __loadLst(name):
    nam, ext = os.path.splitext(os.path.basename(name))
    return List(name)


def __loadGraph(name):
    nam, ext = os.path.splitext(os.path.basename(name))
    return Graph(name)


def __loadImage(name):
    from PIL import Image
    im = Image.open(name)
    w = Wave()
    w.data = np.array(im)
    return w


def __loadPxt(name):
    import igor.packed
    import igor.igorpy
    nam, ext = os.path.splitext(os.path.basename(name))
    (rec, data) = igor.packed.load(name)
    wav = igor.igorpy.Wave(data['root'][nam.encode('utf-8')])
    w = Wave()
    w.data = np.array(wav.data)
    w.data.flags.writeable = True
    note = [s.replace(" ", "").replace("\r", "").split("=") for s in wav.notes.decode().replace("\n\n", "\n").split("\n")]
    w.note = {}
    for n in note:
        if len(n) == 2:
            w.note[n[0].lower()] = n[1]
    if w.data.ndim == 1:
        w.x = wav.axis[0]
    if w.data.ndim >= 2:
        w.x = wav.axis[1]
        w.y = wav.axis[0]
    if w.data.ndim == 3:
        w.x = wav.axis[2]
        w.y = wav.axis[1]
        w.z = wav.axis[0]
    return w


try:
    import dm3_lib as dm3

    def __loadDm3(name):
        data = dm3.DM3(name)
        w = Wave()
        w.data = data.imagedata
        if w.data.ndim == 2:  # image
            w.x = np.arange(0, data.pxsize[0] * w.data.shape[0], data.pxsize[0])
            w.y = np.arange(0, data.pxsize[0] * w.data.shape[1], data.pxsize[0])
        elif w.data.ndim == 3:  # spectrum imaging
            w.data = w.data.transpose(1, 2, 0)
            w.x = np.arange(0, data.pxsize[0] * w.data.shape[0], data.pxsize[0])
            w.y = np.arange(0, data.pxsize[0] * w.data.shape[1], data.pxsize[0])
            e0 = float(data.tags['root.ImageList.1.ImageData.Calibrations.Dimension.2.Origin'])
            de = float(data.tags['root.ImageList.1.ImageTags.EELS Spectrometer.Dispersion (eV/ch)'])
            w.z = np.linspace(-e0, -e0 + de * w.data.shape[2], w.data.shape[2])
        w.note = {}
        try:
            w.note['unit'] = data.pxsize[1]
            w.note['specimen'] = data.info['specimen'].decode()
            w.note['date'] = data.info['acq_date'].decode()
            w.note['mag'] = float(data.info['mag'].decode())
            w.note['time'] = data.info['acq_time'].decode()
            w.note['voltage'] = float(data.info['hv'].decode())
            w.note['mode'] = data.info['mode'].decode()
            w.note['exposure'] = data.tags['root.ImageList.1.ImageTags.DataBar.Exposure Time (s)']
            w.note['hbin'] = data.tags['root.ImageList.1.ImageTags.Acquisition.Parameters.Detector.hbin']
            w.note['vbin'] = data.tags['root.ImageList.1.ImageTags.Acquisition.Parameters.Detector.vbin']
            w.note['delay'] = data.tags['root.ImageList.1.ImageTags.Experiment.Laser.delay']
            w.note['power'] = data.tags['root.ImageList.1.ImageTags.Experiment.Laser.power']
            w.note['scanMode'] = data.tags['root.ImageList.1.ImageTags.Experiment.mode']
        except:
            pass
        return w
except ImportError:
    def __loadDm3(name):
        print("Error: To use .dm3 files, please install dm3_lib module.")

try:
    import pydicom

    def __loadDcm(name):
        data = pydicom.read_file(name)
        return Wave(data.pixel_array)
except ImportError:
    def __loadDcm(name):
        print("Error: To use .dcm files, please install dicom module.")


def addFileLoader(type, func):
    dic[type] = func


def getExtentions():
    return dic.keys()


dic = dict(zip(['.npz', '.lst', '.str', '.val', '.dic', '.pxt', '.grf', '.tif', '.jpg', '.png', '.dm3'], [__loadNpz, __loadLst,
                                                                                                          __loadStr, __loadVal, __loadDic, __loadPxt, __loadGraph, __loadImage, __loadImage, __loadImage, __loadDm3]))
dic[".dcm"] = __loadDcm
