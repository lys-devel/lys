import os,sys
import numpy as np
from .ExtendType import *
from .GraphWindow import Graph

def load(name,load=True):
    try:
        if os.path.isdir(name):
            mkdir(pwd()+'/'+os.path.basename(name))
            __loadFolder(name,pwd()+'/'+os.path.basename(name))
        elif os.path.isfile(name):
            path,ext=os.path.splitext(name)
            res=dic[ext](os.path.abspath(name))
            if load:
                return res
    except Exception:
        sys.stderr.write('Error: Cannot load.\n')

def save(name,nameAs):
    data=load(name)
    data.Save(nameAs)

def __loadFolder(name, path):
    files=os.listdir(name)
    for file in files:
        if os.path.isdir(name+'/'+file):
            mkdir(path+'/'+file)
            __loadFolder(name+'/'+file,path+'/'+file)
        elif os.path.isfile(name+'/'+file):
            nam,ext=os.path.splitext(file)
            data=load(os.path.abspath(name+'/'+file))
            if isinstance(data,Wave):
                data.Save(path+'/'+nam+'.npz')
            if isinstance(data,Graph):
                data.Save(path+'/'+nam+'.grf')
            if isinstance(data,String):
                data.Save(path+'/'+nam+'.str')
            if isinstance(data,Variable):
                data.Save(path+'/'+nam+'.val')
            if isinstance(data,Dict):
                data.Save(path+'/'+nam+'.dic')
            if isinstance(data,List):
                data.Save(path+'/'+nam+'.lst')

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
    try:
        w.note['unit']=data.pxsize[1]
        w.note['specimen']=data.info['specimen'].decode()
        w.note['date']=data.info['acq_date'].decode()
        w.note['mag']=float(data.info['mag'].decode())
        w.note['time']=data.info['acq_time'].decode()
        w.note['voltage']=float(data.info['hv'].decode())
        w.note['mode']=data.info['mode'].decode()
        w.note['exposure']=data.tags['root.ImageList.1.ImageTags.DataBar.Exposure Time (s)']
        w.note['hbin']=data.tags['root.ImageList.1.ImageTags.Acquisition.Parameters.Detector.hbin']
        w.note['vbin']=data.tags['root.ImageList.1.ImageTags.Acquisition.Parameters.Detector.vbin']
    except:
        pass
    return w

def addFileLoader(type, func):
    dic[type]=func

def getExtentions():
    return dic.keys()

dic=dict(zip(['.npz','.lst','.str','.val','.dic','.pxt','.grf','.tif','.jpg','.png','.dm3'],[__loadNpz,__loadLst,__loadStr,__loadVal,__loadDic,__loadPxt,__loadGraph,__loadImage,__loadImage,__loadImage,__loadDm3]))
