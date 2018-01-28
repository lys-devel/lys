#!/usr/bin/env python
import os, sys, shutil, weakref, logging
import numpy as np
import scipy.ndimage
import scipy.signal
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
__home=os.getcwd()
__CDChangeListener=[]
sys.path.append(__home)

def mkdir(name):
    try:
        os.makedirs(name)
    except Exception:
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
    except Exception:
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

class AutoSaved(object):
    def _newobj(self,file):
        return ExtendObject(file)

    def __init__(self,file=None):
        self.obj=None
        self.__file=file
        self.__loadFile=None
        self.__modListener=[]
        res=ExtendObject._GetData(file)
        if res is None:
            self.obj=self._newobj(file)
            self.Save()
        else:
            self.obj=res
        self.obj.addDataChangedListener(self._EmitModified)

    def __setattr__(self,key,value):
        if not key=='obj':
            if self.obj is not None:
                if key in self.obj._vallist():
                    import time
                    print('start')
                    t=time.time()
                    res=self.obj.__setattr__(key,np.array(value))
                    self.Save()
                    print('end',time.time()-t)
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
            newfile=os.path.abspath(file)
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
            return self.__file
        return self.__loadFile
    def Name(self):
        if self.FileName() is None:
            return "untitled"
        else:
            nam,ext=os.path.splitext(os.path.basename(self.FileName()))
            return nam
    def IsConnected(self):
        return self.__file is not None

    def addModifiedListener(self,method):
        self.__modListener.append(weakref.WeakMethod(method))
    def _EmitModified(self):
        for m in self.__modListener:
            if m() is None:
                self.__modListener.remove(m)
            else:
                import time
                t=time.time()
                m()(self)
class Wave(AutoSaved):
    class _wavedata(ExtendObject):
        def _load(self,file):
            tmp=np.load(file)
            self.data=tmp['data']
            self.x=tmp['x']
            self.y=tmp['y']
            self.z=tmp['z']
            self.note=tmp['note']
        def _save(self,file):
            np.savez(file, data=self.data, x=self.x, y=self.y, z=self.z,note=self.note)
        def _vallist(self):
            return ['data','x','y','z','note']
    def _newobj(self,file):
        return self._wavedata(file)
    def __getattribute__(self,key):
        if key=='x' or key=='y' or key=='z':
            val=super().__getattribute__(key)
            index=['x','y','z'].index(key)
            dim=self.data.ndim-index-1
            if self.data.ndim<=index:
                return None
            elif val.ndim==0:
                if self.data.ndim>index:
                    return np.arange(self.data.shape[dim])
                else:
                    return val
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
        else:
            return super().__getattribute__(key)

    def slice(self,pos1,pos2,axis='x'):
        index=['x','y'].index(axis)
        size=pos2[index]-pos1[index]
        x,y=np.linspace(pos1[0], pos2[0], size), np.linspace(pos1[1], pos2[1], size)
        res=scipy.ndimage.map_coordinates(self.data, np.vstack((x,y)))
        w=Wave()
        w.data=res
        w.x=self.x[pos1[index]:pos2[index]]
        return w
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
    def posToPoint(self,pos):
        x0=self.x[0]
        x1=self.x[len(self.x)-1]
        y0=self.y[0]
        y1=self.y[len(self.y)-1]
        dx=(x1-x0)/(self.data.shape[1]-1)
        dy=(y1-y0)/(self.data.shape[0]-1)
        return (int(round((pos[0]-x0)/dx)),int(round((pos[1]-y0)/dy)))
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
    closed=pyqtSignal()
    def __init__(self):
        super().__init__()
    def resizeEvent(self,event):
        self.resized.emit()
        return super().resizeEvent(event)
    def moveEvent(self,event):
        self.moved.emit()
        return super().moveEvent(event)
    def closeEvent(self,event):
        self.closed.emit()
        return super().closeEvent(event)
class ExtendMdiSubWindow(AttachableWindow):
    mdimain=None
    __wins=[]
    def __init__(self, title=None):
        logging.debug('[ExtendMdiSubWindow] __init__')
        super().__init__()
        ExtendMdiSubWindow._AddWindow(self)
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
    def _AddWindow(cls,win):
        cls.__wins.append(win)
        if cls.mdimain is not None:
            cls.mdimain.addSubWindow(win)
    @classmethod
    def _RemoveWindow(cls,win):
        cls.__wins.remove(win)
        cls.mdimain.removeSubWindow(win)
    @classmethod
    def _Contains(cls,win):
        return win in cls.__wins
    @classmethod
    def AllWindows(cls):
        return cls.__wins
    def closeEvent(self,event):
        ExtendMdiSubWindow._RemoveWindow(self)
        super().closeEvent(event)

class AutoSavedWindow(ExtendMdiSubWindow):
    __list=List(home()+'/.lys/winlist.lst')
    _isclosed=False
    _restore=False
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
    @classmethod
    def RestoreAllWindows(cls):
        from . import LoadFile
        cls._restore=True
        mkdir(home()+'/.lys/wins')
        for path in cls.__list.data:
            try:
                w=LoadFile.load(path)
                if path.find(home()+'/.lys/wins') > -1:
                    w.Disconnect()
            except:
                pass
        cls._restore=False
    @classmethod
    def StoreAllWindows(cls):
        cls._isclosed=True
        for w in cls.AllWindows():
            w.close()
        cls._isclosed=False
    @classmethod
    def _IsClosed(cls):
        return cls._isclosed
    def _onRestore(cls):
        return cls._restore
    def NewTmpFilePath(self):
        mkdir(home()+'/.lys/wins')
        for i in range(1000):
            path=home()+'/.lys/wins/'+self._prefix()+str(i).zfill(3)+self._suffix()
            if not AutoSavedWindow._IsUsed(path):
                return path
        print('Too many windows.')
    def __new__(cls, file=None, title=None):
        logging.debug('[AutoSavedWindow] __new__ called.')
        if cls._restore:
            return super().__new__(cls)
        if AutoSavedWindow._IsUsed(file):
            logging.debug('[AutoSavedWindow] found loaded window.')
            return None
        return super().__new__(cls)
    def __init__(self, file=None, title=None):
        logging.debug('[AutoSavedWindow] __init__ called.')
        try:
            self.__file
        except Exception:
            logging.debug('[AutoSavedWindow] new window will be created.')
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
            self._init()
            self.__Load(self.__file)
            self.Save()
            AutoSavedWindow._AddAutoWindow(self)
    def setLoadFile(self,file):
        self.__loadFile=os.path.abspath(file)
    def __Load(self,file):
        logging.debug('[AutoSavedWindow] __Load called.')
        if file is not None:
            self.__file=os.path.abspath(file)
        if os.path.exists(self.__file):
            self._load(self.__file)

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
            self._save(file)
            self.__isTmp=False
        else:
            self._save(self.__file)

    def closeEvent(self,event):
        if (not AutoSavedWindow._IsClosed()) and (not self.IsConnected()):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("This window is not saved. Do you really want to close it?")
            msg.setWindowTitle("Caution")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ok = msg.exec_()
            if ok==QMessageBox.Cancel:
                event.ignore()
                return
        if not AutoSavedWindow._IsClosed():
            AutoSavedWindow._RemoveAutoWindow(self)
            if not self.IsConnected():
                remove(self.__file)
        return super().closeEvent(event)
