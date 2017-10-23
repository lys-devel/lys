import os,sys
import numpy as np
from .ExtendType import *
from .GraphWindow import Graph

def load(name,load=True):
    try:
        if os.path.isfile(name):
            path,ext=os.path.splitext(name)
            res=dic[ext](name)
            if load:
                return res
    except Exception:
        sys.stderr.write('Error: Cannot load.\n')

def save(name,nameAs):
    data=load(name)
    data.Save(nameAs)

def __loadNpz(name):
    nam,ext=os.path.splitext(os.path.basename(name))
    return Wave(name)

def __loadStr(name):
    nam,ext=os.path.splitext(os.path.basename(name))
    return String(name)

def __loadVal(name):
    nam,ext=os.path.splitext(os.path.basename(name))
    return Variable(name)

def __loadDic(name):
    nam,ext=os.path.splitext(os.path.basename(name))
    return Dict(name)

def __loadLst(name):
    nam,ext=os.path.splitext(os.path.basename(name))
    return List(name)

def __loadGraph(name):
    nam,ext=os.path.splitext(os.path.basename(name))
    return Graph(name)

def __loadImage(name):
    from PIL import Image
    im=Image.open(name)
    w=Wave()
    w.data=np.array(im)
    return w

def __loadPxt(name):
    import igor.packed, igor.igorpy
    nam,ext=os.path.splitext(os.path.basename(name))
    (rec,data)=igor.packed.load(name)
    wav=igor.igorpy.Wave(data['root'][nam.encode('utf-8')])
    w=Wave()
    w.data=wav.data
    w.x=wav.axis[0]
    w.note=wav.notes.decode()
    if w.data.ndim>=2:
        w.y=wav.axis[1]
    if w.data.ndim>=3:
        w.z=wav.axis[2]
    return w

def __loadDm3(name):
    import dm3_lib as dm3
    data = dm3.DM3(name)
    w=Wave()
    w.data=data.imagedata
    w.x=np.arange(0,data.pxsize[0]*w.data.shape[0],data.pxsize[0])
    if w.data.ndim>=2:
        w.y=np.arange(0,data.pxsize[0]*w.data.shape[1],data.pxsize[0])
    w.note={}
    w.note['unit']=data.pxsize[1]
    w.note['specimen']=data.info['specimen'].decode()
    w.note['date']=data.info['acq_date'].decode()
    w.note['mag']=float(data.info['mag'].decode())
    w.note['time']=data.info['acq_time'].decode()
    w.note['voltage']=float(data.info['hv'].decode())
    w.note['mode']=data.info['mode'].decode()
    return w

def addFileLoader(type, func):
    dic[type]=func

def getExtentions():
    return dic.keys()

dic=dict(zip(['.npz','.lst','.str','.val','.dic','.pxt','.grf','.tif','.jpg','.png','.dm3'],[__loadNpz,__loadLst,__loadStr,__loadVal,__loadDic,__loadPxt,__loadGraph,__loadImage,__loadImage,__loadImage,__loadDm3]))
