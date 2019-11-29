#!/usr/bin/env python
import os, sys, shutil, weakref, logging, unittest
import numpy as np
import scipy.ndimage
import scipy.signal
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import inspect
__home=os.getcwd()
__CDChangeListener=[]
sys.path.append(__home)

def mkdir(name):
    if os.path.exists(name):
        return
    try:
        os.makedirs(name)
    except:
        pass
def copy(name,name_to):
    try:
        if os.path.isdir(name):
            mkdir(name_to)
            lis=os.listdir(name)
            for item in lis:
                copy(name+'/'+item,name_to+'/'+item)
        else:
            if not os.path.exists(name_to):
                shutil.copy(name,name_to)
            else:
                sys.stderr.write('Error: Cannot copy. This file exists.\n')
    except:
        sys.stderr.write('Error: Cannot remove.\n')
def move(name,name_to):
    if os.path.abspath(name_to).find(os.path.abspath(name))>-1:
        sys.stderr.write('Error: Cannot move. The file cannot be moved to this folder.\n')
        return 0
    try:
        if os.path.isdir(name):
            mkdir(name_to)
            lis=os.listdir(name)
            for item in lis:
                move(name+'/'+item,name_to+'/'+item)
            remove(name)
        else:
            if not os.path.exists(name_to):
                shutil.move(name,name_to)
                ExtendObject.OnMoveFile(name,name_to)
            else:
                sys.stderr.write('Error: Cannot move. This file exists.\n')
    except Exception:
        sys.stderr.write('Error: Cannot move.\n')
def remove(name):
    try:
        if os.path.isdir(name):
            lis=os.listdir(name)
            for item in lis:
                remove(name+'/'+item)
            os.rmdir(name)
        else:
            if ExtendObject._GetData(os.path.abspath(name)) is None:
                os.remove(name)
            else:
                sys.stderr.write('Error: Cannot remove. This file is in use.\n')
    except Exception:
        sys.stderr.write('Error: Cannot remove.\n')
def pwd():
    return os.getcwd()
def cd(direct=None):
    if direct is None or len(direct)==0:
        direct=__home
    os.chdir(direct)
    for listener in __CDChangeListener:
        listener.OnCDChanged(pwd())
def home():
    return __home
def addCDChangeListener(listener):
    __CDChangeListener.append(listener)
    listener.OnCDChanged(pwd())
def globalSetting():
    return Dict(home()+"/.lys/settings/global.dic")

class ExtendObject(object):
    __dic={}
    @classmethod#TODO
    def OnMoveFile(cls,file,file_to):
        if cls.IsUsed(os.path.abspath(file)):
            cls.__dic[os.path.abspath(file)]()._Connect(os.path.abspath(file_to))
            cls._Remove(file)
    @classmethod
    def _Append(cls,file,data):
        cls.__dic[os.path.abspath(file)]=weakref.ref(data)
    @classmethod
    def _GetData(cls,file):
        try:
            abs=os.path.abspath(file)
        except:
            return None
        if not abs in cls.__dic:
            return None
        res=cls.__dic[abs]()
        if res is None:
            del cls.__dic[abs]
        return res
    @classmethod
    def Reload(cls,list=[]):
        for ref in cls.__dic.values():
            o=ref()
            if o is not None:
                try:
                    o._load(o._filename())
                    o._emitDataChanged()
                except:
                    logging.error("[ExtendObject] Failed to reload. Restart is recommended.")
    def __init__(self,file):
        self.__file=file
        self.__init(file)
        if file is not None:
            ExtendObject._Append(file,self)
        self.__listener=[]
    def addDataChangedListener(self,listener):
        self.__listener.append(weakref.WeakMethod(listener))
    def removeDataChangedListener(self,listener):
        for l in self.__listener:
            if l()==listener:
                self.__listener.remove(l)
    def _emitDataChanged(self):
        for l in self.__listener:
            if l() is None:
                self.__listener.remove(l)
            else:
                l()()
    def Save(self,file):
        abspath=os.path.abspath(file)
        mkdir(os.path.dirname(abspath))
        obj=ExtendObject._GetData(file)
        if obj is None:
            ExtendObject._Append(file,self)
            self._save(file)
            self._emitDataChanged()
            return self
        elif obj==self:
            self._save(file)
            self._emitDataChanged()
            return self
        else:
            obj.__overwrite(file,self)
            obj._emitDataChanged()
            return obj
    def __overwrite(self,file,target):
        for key in self._vallist():
            self.__setattr__(key,target.__getattribute__(key))
        self._save(file)
    def __init(self,file):
        if file is None:
            self._init()
        else:
            if not os.path.exists(os.path.abspath(file)):
                self._init()
            else:
                self._load(file)

    def _init(self):
        for l in self._vallist():
            self.__setattr__(l,None)
    def _load(self,file):
        with open(file,'r') as f:
            self.data=eval(f.read())
    def _save(self,file):
        with open(file,'w') as f:
            f.write(str(self.data))
    def _vallist(self):
        return ['data']
    def _filename(self):
        return self.__file

class AutoSaved(object):
    def _newobj(self,file):
        return ExtendObject(file)

    def __init__(self,file=None):
        self.obj=None
        self.__name=None
        self.__file=self._parseFilename(file)
        self.__loadFile=None
        self.__modListener=[]
        res=ExtendObject._GetData(self.__file)
        if res is None:
            self.obj=self._newobj(self.__file)
            #self.Save()##Note: it is modified 12/24
        else:
            self.obj=res
        self.obj.addDataChangedListener(self._EmitModified)
    def _parseFilename(self,path):
        return path
    def __setattr__(self,key,value):
        if not key=='obj':
            if self.obj is not None:
                if key in self.obj._vallist():
                    res=self.obj.__setattr__(key,value)
                    self.Save()
                    return res
        super().__setattr__(key,value)
    def __getattribute__(self,key):
        if key=='obj':
            return super().__getattribute__(key)
        if self.obj is not None:
            if key in self.obj._vallist():
                return self.obj.__getattribute__(key)
        return super().__getattribute__(key)

    def Save(self,file=None):
        if file is not None:
            newfile=os.path.abspath(self._parseFilename(file))
            if not self.__file==newfile:
                if self.__file is not None:
                    self.Disconnect()
                self.__file=newfile
        if self.__file is not None:
            tmp=self.obj.Save(self.__file)
            if not tmp==self.obj:
                self.obj.removeDataChangedListener(self._EmitModified)
                tmp.addDataChangedListener(self._EmitModified)
                self.obj=tmp
                self._EmitModified()
            return True
        else:
            self._EmitModified()
            return False
    def Disconnect(self):
        newobj=self._newobj(None)
        for key in newobj._vallist():
            newobj.__setattr__(key,self.obj.__getattribute__(key))
        self.obj.removeDataChangedListener(self._EmitModified)
        newobj.addDataChangedListener(self._EmitModified)
        self.obj=newobj
        self._EmitModified()
        self.__file=None

    def setLoadFile(self,file):
        self.__loadFile=os.path.abspath(file)
    def FileName(self):
        if self.__file is not None:
            return os.path.abspath(self.__file)
        return self.__loadFile
    def Name(self):
        if self.__name is not None:
            return self.__name
        elif self.FileName() is None:
            return "untitled"
        else:
            nam,ext=os.path.splitext(os.path.basename(self.FileName()))
            return nam
    def SetName(self,name):
        self.__name=name
    def IsConnected(self):
        return self.__file is not None

    def addModifiedListener(self,method):
        self.__modListener.append(weakref.WeakMethod(method))
    def _EmitModified(self):
        for m in self.__modListener:
            if m() is None:
                self.__modListener.remove(m)
            else:
                m()(self)
def produce(data,axes,note):
    w=Wave()
    w.data=data
    w.axes=axes
    w.note=note
    return w
class Wave(AutoSaved):
    class _wavedata(ExtendObject):
        def _init(self):
            self.axes=[np.array(None)]
            self.data=np.array(None)
            self.note={}
        def _load(self,file):
            tmp=np.load(file,allow_pickle=True)
            self.axes=[np.array(None) for i in range(tmp['data'].ndim)]
            if 'axes' in tmp:
                self._load_new(tmp)
            else:
                self._load_old(tmp)
            if 'note' in tmp:
                self.note = tmp['note'][()]
            else:
                self.note = {}
        def _load_new(self,tmp):
            self.data=tmp['data']
            if 'axes' in tmp:
                self.axes=tmp['axes']
        def _load_old(self,tmp):
            self.data=tmp['data'].T
            if self.data.ndim==1:
                self.axes[0]=tmp['x']
            if self.data.ndim==2:
                self.axes[0]=tmp['x']
                self.axes[1]=tmp['y']
            if self.data.ndim==3:
                self.axes[0]=tmp['x']
                self.axes[1]=tmp['y']
                self.axes[2]=tmp['z']
        def _save(self,file):
            np.savez(file, data=self.data, axes=self.axes,note=self.note, allow_pickle = True)
        def _vallist(self):
            return ['data','x','y','z','note','axes']
        def __setattr__(self,key,value):
            if key == 'x' and len(self.axes) > 0:
                self.axes[0]=np.array(value)
            elif key == 'y' and len(self.axes) > 1:
                self.axes[1]=np.array(value)
            elif key == 'z' and len(self.axes) > 2:
                self.axes[2]=np.array(value)
            elif key in ['data']:
                super().__setattr__(key,np.array(value))
                while(len(self.axes) < self.data.ndim): self.axes.append(np.array(None))
                while(len(self.axes) > self.data.ndim): self.axes.pop(len(self.axes)-1)
            else:
                super().__setattr__(key,value)
        def __getattribute__(self,key):
            if key == 'x':
                if len(self.axes) > 0:
                    return self.axes[0]
                else:
                    return np.array(None)
            if key == 'y':
                if len(self.axes) > 1:
                    return self.axes[1]
                else:
                    return np.array(None)
            if key == 'z':
                if len(self.axes) > 2:
                    return self.axes[2]
                else:
                    return np.array(None)
            return super().__getattribute__(key)
    def _newobj(self,file):
        return self._wavedata(file)
    def __getattribute__(self,key):
        if key=='x' or key=='y' or key=='z':
            val=super().__getattribute__(key)
            index=['x','y','z'].index(key)
            return self.getAxis(index)
        else:
            return super().__getattribute__(key)
    def getAxis(self,dim):
        val = np.array(self.axes[dim])
        if self.data.ndim <= dim:
            return None
        elif val.ndim==0:
            return np.arange(self.data.shape[dim])
        else:
            if self.data.shape[dim]==val.shape[0]:
                return val
            else:
                res=np.empty((self.data.shape[dim]))
                for i in range(self.data.shape[dim]):
                    res[i]=np.NaN
                for i in range(min(self.data.shape[dim],val.shape[0])):
                    res[i]=val[i]
                return res
    def __getitem__(self,key):
        if isinstance(key,tuple):
            data=self.data[key]
            axes=[]
            for s, ax in zip(key,self.axes):
                axes.append(ax[s])
            w=Wave()
            w.data=data
            w.axes=axes
            return w
        else:
            super().__getitem__(key)
    def __setitem__(self,key,value):
        self.data[key]=value
        self.Save()
    def __reduce_ex__(self,proto):
        if self.IsConnected():
            return Wave,(self.FileName())
        else:
            return produce,(self.data,self.axes,self.note)
    def _parseFilename(self,path):
        if path is None:
            return None
        return (path+".npz").replace(".npz.npz",".npz")
    def slice(self,pos1,pos2,axis='x',width=1):
        w=Wave()
        dx=(pos2[0]-pos1[0])
        dy=(pos2[1]-pos1[1])
        index=['x','y','xy'].index(axis)
        if index==2:
            size=int(np.sqrt(dx*dx+dy*dy)+1)
        else:
            size=abs(pos2[index]-pos1[index])+1
        res=np.zeros((size))
        nor=np.sqrt(dx*dx+dy*dy)
        dx, dy = dy/nor, -dx/nor
        for i in range(1-width,width,2):
            x,y = np.linspace(pos1[0], pos2[0], size) + dx*(i*0.5), np.linspace(pos1[1], pos2[1], size)+ dy*(i*0.5)
            res += scipy.ndimage.map_coordinates(self.data, np.vstack((y,x)),mode="constant",order=3,prefilter=True)
        w.data=res
        if axis == 'x':
            w.x=self.x[pos1[index]:pos2[index]+1]
        elif axis == 'y':
            w.x=self.y[pos1[index]:pos2[index]+1]
        else:
            dx=abs(self.x[pos1[0]]-self.x[pos2[0]])
            dy=abs(self.y[pos1[1]]-self.y[pos2[1]])
            d=np.sqrt(dx*dx+dy*dy)
            w.x=np.linspace(0,d,size)
        return w
    def integrate(self,region,type='circle',dr=1):
        if type == 'circle':
            return self._integrate_circle(region)
        if type == 'tangent':
            return self._integrate_tangent(region,dr)
    def _integrate_tangent(self,region,dr):
        w=Wave()
        w.data=[self.integrate((region[0],region[1],r,r+dr)) for r in range(region[2],region[3],dr)]
        dx=self.x[1]-self.x[0]
        w.x=np.linspace(0,len(w.data)*dr*dx,num=len(w.data))
        return w
    def _integrate_circle(self,region):
        cx=region[0]
        cy=region[1]
        R1=region[2]
        R2=region[3]
        res=0
        n=0
        for px in self._calcDonutPixels(R1,R2):
            a=abs(px[0])-0.5
            b=abs(px[1])-0.5
            if a < b:
                a,b=b,a
            x,y = cx+px[0], cy+px[1]
            if x > 0 and y > 0 and x < self.data.shape[1] and y < self.data.shape[0]:
                rat=self._calcArea(a,b,R2)-self._calcArea(a,b,R1)
                res+=self.data[y,x]*rat
                n+=rat
        return res/n
    def _calcArea(self,a,b,r):
        if r==0: return 0
        if np.sqrt((a+1)*(a+1)+(b+1)*(b+1)) <= r:
            return 1
        elif np.sqrt(a*a+b*b) <= r and np.sqrt(a*a+(b+1)*(b+1)) >= r:
            b1=np.sqrt(r*r-a*a)
            return self._int(r,b,b1)-a*(b1-b)
        elif np.sqrt(a*a+(b+1)*(b+1)) <= r and np.sqrt((a+1)*(a+1)+b*b) >= r:
            return self._int(r,b,b+1)-a
        elif np.sqrt((a+1)*(a+1)+b*b) <= r and np.sqrt((a+1)*(a+1)+(b+1)*(b+1)) > r:
            b1=np.sqrt(r*r-(a+1)*(a+1))
            return (b1-b)+self._int(r,b1,b+1)-a*(b+1-b1)
        elif np.sqrt(a*a+b*b) > r:
            return 0
    # calc int_a^b sqrt(r^2-x^2) dx
    def _int(self,r,a,b):
        return 0.5*(b*np.sqrt(r*r-b*b)+r*r*np.arcsin(b/r)-a*np.sqrt(r*r-a*a)-r*r*np.arcsin(a/r))

    def _calcDonutPixels(self,R1,R2):
        res=[]
        for y1 in range( -int(np.floor(R2+0.5)) , int(np.floor(R2+0.5)+1)):
            y1_R1=self._calcCross(y1,R1)
            y1_R2=self._calcCross(y1,R2)
            y1p_R1=self._calcCross(y1+0.5,R1)
            y1p_R2=self._calcCross(y1+0.5,R2)
            y1m_R1=self._calcCross(y1-0.5,R1)
            y1m_R2=self._calcCross(y1-0.5,R2)
            if y1m_R1 * y1p_R1==0:
                xmin=0
            else:
                xmin=int(np.round(np.amin([y1_R1,y1p_R1,y1m_R1])))
            xmax=int(np.round(np.amax([y1_R2,y1p_R2,y1m_R2])))
            for x1 in range(xmin,xmax+1):
                res.append((x1,y1))
            for x1 in range(-xmax,-xmin+1):
                if x1!=0:
                    res.append((x1,y1))
        return res
    def _calcCross(self,y,R):
        if abs(y) > R:
            return 0
        else:
            return np.sqrt(R*R-y*y)
    def getSlicedImage(self,zindex):
        return self.data[:,:,zindex]

    def var(self,*args):
        dim=len(args)
        if len(args)==0:
            return self.data.var()
    def smooth(self,cutoff):#cutoff is from 0 to 1 (relative to nikist frequency)
        b, a = scipy.signal.butter(1,cutoff)
        w=Wave()
        w.data=self.data
        for i in range(0,self.data.ndim):
            w.data=scipy.signal.filtfilt(b,a,w.data,axis=i)
        return w
    def differentiate(self):
        w=Wave()
        w.data=self.data
        w.x=self.x
        w.y=self.y
        for i in range(0,w.data.ndim):
            w.data=np.gradient(self.data)[i]
        return w

    def sum(self,axis):
        w=Wave()
        w.data=self.data.sum(axis)
        axes=[]
        for i, ax in enumerate(self.axes):
            if not i == axis:
                axes.append(ax)
        w.axes=axes
        return w
    def average(self,*args):
        dim=len(args)
        if len(args)==0:
            return self.data.mean()
        if not dim==self.data.ndim:
            return 0
        if dim==1:
            return self.__average1D(args[0])
        if dim==2:
            return self.__average2D(args[0],args[1])
    def posToPoint(self,pos,axis=None):
        if axis is None:
            x0=self.x[0]
            x1=self.x[len(self.x)-1]
            y0=self.y[0]
            y1=self.y[len(self.y)-1]
            dx=(x1-x0)/(len(self.x)-1)
            dy=(y1-y0)/(len(self.y)-1)
            return (int(round((pos[0]-x0)/dx)),int(round((pos[1]-y0)/dy)))
        else:
            ax = self.getAxis(axis)
            x0=ax[0]
            x1=ax[len(ax)-1]
            dx=(x1-x0)/(len(ax)-1)
            return int(round((pos-x0)/dx))
    def pointToPos(self,p):
        x0=self.x[0]
        x1=self.x[len(self.x)-1]
        y0=self.y[0]
        y1=self.y[len(self.y)-1]
        dx=(x1-x0)/(len(self.x)-1)
        dy=(y1-y0)/(len(self.y)-1)
        return (p[0]*dx+x0,p[1]*dy+y0)
    def copy(self):
        w=Wave()
        w.data=self.data
        w.x=self.x
        w.y=self.y
        w.z=self.z
        w.note=self.note
    def __average1D(self,range):
        return self.data[range[0]:range[1]+1].sum()/(range[1]-range[0]+1)
    def __average2D(self,range1,range2):
        return self.data[int(range2[0]):int(range2[1])+1,int(range1[0]):int(range1[1])+1].sum()/(range1[1]-range1[0]+1)/(range2[1]-range2[0]+1)
    def shape(self):
        res=[]
        tmp=self.data.shape
        for i in tmp:
            if i is not None:
                res.append(i)
        return tuple(res)
    @staticmethod
    def SupportedFormats():
        return ["Numpy npz (*.npz)","Comma-Separated Values (*.csv)"]
    def export(self,path,type="Numpy npz (*.npz)"):
        if type == 'Numpy npz (*.npz)':
            np.savez(path+".npz".replace(".npz.npz",".npz"), data=self.data, axes = self.axes, note=self.note)
        if type == "Comma-Separated Values (*.csv)":
            import csv
            with open(path+".csv".replace(".csv.csv",".csv"),'w') as f:
                writer=csv.writer(f,lineterminator='\n')
                writer.writerows(self.data)
    @staticmethod
    def importFrom(path):
        p,ext=os.path.splitext(path)
        if ext=="npz":
            w=Wave(path)
            w.Disconnect()
            return w
        else:
            data=np.loadtxt(path,delimiter=",")
            w=Wave()
            w.data=data
            return w

class String(AutoSaved):
    class _stringdata(ExtendObject):
        def _load(self,file):
            with open(file,'r') as f:
                self.data=f.read()
        def _init(self):
            self.data=''
    def _newobj(self,file):
        return self._stringdata(file)
    def __setattr__(self,key,value):
        if key=='data':
            super().__setattr__(key,str(value))
        else:
            super().__setattr__(key,value)

class Variable(AutoSaved):
    class _valdata(ExtendObject):
        def _init(self):
            self.data=0
    def _newobj(self,file):
        return self._valdata(file)
class Dict(AutoSaved):
    class _dicdata(ExtendObject):
        def _init(self):
            self.data={}
    def _newobj(self,file):
        return self._dicdata(file)
    def __getitem__(self,key):
        return self.data[key]
    def __setitem__(self,key,value):
        self.data[key]=value
        self.Save()
    def __delitem__(self,key):
        del self.data[key]
        self.Save()
    def __missing__(self,key):
        return None
    def __contains__(self,key):
        return key in self.data
    def __len__(self):
        return len(self.data)

class List(AutoSaved):
    class _listdata(ExtendObject):
        def _init(self):
            self.data=[]
    def _newobj(self,file):
        return self._listdata(file)
    def __getitem__(self,key):
        return self.data[key]
    def __setitem__(self,key,value):
        self.data[key]=value
        self.Save()
    def append(self,value):
        self.data.append(value)
        self.Save()
    def remove(self,value):
        self.data.remove(value)
        self.Save()
    def __contains__(self,key):
        return key in self.data
    def __len__(self):
        return len(self.data)
    def shape(self):
        res=[]
        d=self.data
        while isinstance(d,list) or isinstance(d,List):
            res.append(len(d))
            if len(d) > 0:
                d=d[0]
            else:
                break
        return tuple(res)
    @staticmethod
    def SupportedFormats():
        return ["Lys List file (*.lst)","Comma-Separated Values (*.csv)"]
    def export(self,path,type="Lys List file (*.lst)"):
        if type == "Lys List file (*.lst)":
            l=List()
            l.data=self.data
            l.Save(path+".lst".replace(".lst.lst",".lst"))
        if type == "Comma-Separated Values (*.csv)":
            import csv
            with open(path+".csv".replace(".csv.csv",".csv"),'w') as f:
                writer=csv.writer(f,lineterminator='\n')
                writer.writerows(self.data)

class ExtendMdiSubWindowBase(QMdiSubWindow):
    pass
class SizeAdjustableWindow(ExtendMdiSubWindowBase):
    def __init__(self):
        super().__init__()
        #Mode #0 : Auto, 1 : heightForWidth, 2 : widthForHeight
        self.__mode=0
        self.__aspect=0
        self.setWidth(0)
        self.setHeight(0)
        self.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
    def setWidth(self,val):
        if self.__mode==2:
            self.__mode=0
        if val==0:
            self.setMinimumWidth(35)
            self.setMaximumWidth(100000)
        else:
            self.setMinimumWidth(val)
            self.setMaximumWidth(val)
    def setHeight(self,val):
        if self.__mode==1:
            self.__mode=0
        if val==0:
            self.setMinimumHeight(35)
            self.setMaximumHeight(100000)
        else:
            self.setMinimumHeight(val)
            self.setMaximumHeight(val)

class AttachableWindow(SizeAdjustableWindow):
    resized=pyqtSignal()
    moved=pyqtSignal()
    closed=pyqtSignal(object)
    def __init__(self):
        super().__init__()
        self._parent=None
    def resizeEvent(self,event):
        self.resized.emit()
        return super().resizeEvent(event)
    def moveEvent(self,event):
        self.moved.emit()
        return super().moveEvent(event)
    def _attach(self,parent):
        self._parent=parent
        if isinstance(parent,ExtendMdiSubWindow):
            self._parent.moved.connect(self.attachTo)
            self._parent.resized.connect(self.attachTo)
            self._parent.closed.connect(self.close)
    def closeEvent(self,event):
        if self._parent is not None:
            self._parent.moved.disconnect(self.attachTo)
            self._parent.resized.disconnect(self.attachTo)
            self._parent.closed.disconnect(self.close)
        self.closed.emit(self)
        return super().closeEvent(event)
    def attachTo(self):
        if self._parent is not None:
            pos=self._parent.pos()
            frm=self._parent.frameGeometry()
            self.move(QPoint(pos.x()+frm.width(),pos.y()))
class ExtendMdiSubWindow(AttachableWindow):
    mdimain=None
    __wins=[]
    def __init__(self, title=None, floating=False):
        logging.debug('[ExtendMdiSubWindow] __init__')
        super().__init__()
        self.__floating=floating
        ExtendMdiSubWindow._AddWindow(self,floating)
        self.setAttribute(Qt.WA_DeleteOnClose)
        if title is not None:
            self.setWindowTitle(title)
        self.updateGeometry()
        self.show()
    @classmethod
    def CloseAllWindows(cls):
        for g in cls.__wins:
            g.close()
    @classmethod
    def _AddWindow(cls,win,floating):
        cls.__wins.append(win)
        if cls.mdimain is not None and not floating:
            cls.mdimain.addSubWindow(win)
    @classmethod
    def _RemoveWindow(cls,win,floating):
        cls.__wins.remove(win)
        if not floating:
            cls.mdimain.removeSubWindow(win)
    @classmethod
    def _Contains(cls,win):
        return win in cls.__wins
    @classmethod
    def AllWindows(cls):
        return cls.__wins
    def closeEvent(self,event):
        ExtendMdiSubWindow._RemoveWindow(self,self.__floating)
        super().closeEvent(event)

_workspace="default"
_windir=home()+'/.lys/workspace/'+_workspace+'/wins'
class AutoSavedWindow(ExtendMdiSubWindow):
    __list=None
    _isclosed=False
    _restore=False
    folder_prefix=home()+'/.lys/workspace/'
    @classmethod
    def _IsUsed(cls,path):
        return path in cls.__list.data
    @classmethod
    def _AddAutoWindow(cls,win):
        if not win.FileName() in cls.__list.data:
            cls.__list.append(win.FileName())
    @classmethod
    def _RemoveAutoWindow(cls,win):
        if win.FileName() in cls.__list.data:
            cls.__list.remove(win.FileName())
            if not win.IsConnected():
                remove(win.FileName())
    @classmethod
    def SwitchTo(cls,workspace='default'):
        if workspace=="":
            workspace="default"
        cls.StoreAllWindows()
        cls.RestoreAllWindows(workspace)
    @classmethod
    def RestoreAllWindows(cls,workspace='default'):
        from . import LoadFile
        AutoSavedWindow._workspace=workspace
        #please delete after replacing winlist
        oldpath=home()+'./.lys/winlist.lst'
        newpath=home()+'/.lys/workspace/'+AutoSavedWindow._workspace+'/winlist.lst'
        if os.path.exists(oldpath) and not os.path.exists(newpath):
            copy(oldpath,newpath)
        #################################
        cls.__list=List(home()+'/.lys/workspace/'+AutoSavedWindow._workspace+'/winlist.lst')
        AutoSavedWindow._windir=home()+'/.lys/workspace/'+AutoSavedWindow._workspace+'/wins'
        print("Workspace: "+AutoSavedWindow._workspace)
        cls._restore=True
        mkdir(_windir)
        for path in cls.__list.data:
            try:
                w=LoadFile.load(path)
                if path.find(_windir) > -1:
                    w.Disconnect()
            except:
                pass
        cls._restore=False
    @classmethod
    def StoreAllWindows(cls):
        cls._isclosed=True
        list=cls.mdimain.subWindowList(order=QMdiArea.ActivationHistoryOrder)
        for l in reversed(list):
            if isinstance(l,AutoSavedWindow):
                l.close(force=True)
        cls._isclosed=False
    @classmethod
    def _IsClosed(cls):
        return cls._isclosed
    def _onRestore(cls):
        return cls._restore
    def NewTmpFilePath(self):
        mkdir(AutoSavedWindow._windir)
        for i in range(1000):
            path=AutoSavedWindow._windir+'/'+self._prefix()+str(i).zfill(3)+self._suffix()
            if not AutoSavedWindow._IsUsed(path):
                return path
        print('Too many windows.')
    def __new__(cls, file=None, title=None, **kwargs):
        logging.debug('[AutoSavedWindow] __new__ called.')
        if cls._restore:
            return super().__new__(cls)
        if AutoSavedWindow._IsUsed(file):
            logging.debug('[AutoSavedWindow] found loaded window.', file)
            return None
        return super().__new__(cls)
    def __init__(self, file=None, title=None, **kwargs):
        logging.debug('[AutoSavedWindow] __init__ called.')
        try:
            self.__file
        except Exception:
            logging.debug('[AutoSavedWindow] new window will be created.')
            self.__closeflg=True
            if file is None:
                logging.debug('[AutoSavedWindow] file is None. New temporary window is created.')
                self.__isTmp=True
                self.__file=self.NewTmpFilePath()
            else:
                logging.debug('[AutoSavedWindow] file is ' + file + '.')
                self.__isTmp=False
                self.__file=file
            if title is not None:
                super().__init__(title)
            else:
                super().__init__(self.Name())
            if file is not None:
                self.__file=os.path.abspath(file)
            if os.path.exists(self.__file) and not self.__isTmp:
                self._init(self.__file,**kwargs)
            else:
                self._init(**kwargs)
            AutoSavedWindow._AddAutoWindow(self)
    def setLoadFile(self,file):
        self.__loadFile=os.path.abspath(file)
    def FileName(self):
        return self.__file
    def Name(self):
        nam,ext=os.path.splitext(os.path.basename(self.FileName()))
        return nam
    def IsConnected(self):
        return not self.__isTmp
    def Disconnect(self):
        self.__isTmp=True
    def Save(self,file=None):
        if file is not None:
            AutoSavedWindow._RemoveAutoWindow(self)
            self.__file=os.path.abspath(file)
            mkdir(os.path.dirname(file))
            self._save(self.__file)
            self.__isTmp=False
            title=os.path.basename(file)
            self.setWindowTitle(title)
            AutoSavedWindow._AddAutoWindow(self)
        else:
            self._save(self.__file)
    def close(self, force=False):
        if force:
            self.__closeflg=False
        else:
            self.__closeflg=True
        super().close()
    def closeEvent(self,event):
        if (not AutoSavedWindow._IsClosed()) and (not self.IsConnected()) and self.__closeflg:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("This window is not saved. Do you really want to close it?")
            msg.setWindowTitle("Caution")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ok = msg.exec_()
            if ok==QMessageBox.Cancel:
                event.ignore()
                return
        self.Save()
        if not AutoSavedWindow._IsClosed():
            AutoSavedWindow._RemoveAutoWindow(self)
        return super().closeEvent(event)

if __name__ == "__main__":
    unittest.main()
