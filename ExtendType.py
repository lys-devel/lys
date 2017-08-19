#!/usr/bin/env python
import os, sys, shutil, weakref
import numpy as np
import scipy.ndimage
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

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
                _DataManager.OnMoveFile(name,name_to)
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
            if not _DataManager.IsUsed(os.path.abspath(name)):
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
def addCDChangeListener(listener):
    __CDChangeListener.append(listener)
    listener.OnCDChanged(pwd())

class _DataManager(object):
    __dic={}

    @classmethod
    def IsUsed(cls,file):
        if file is None:
            return False
        return os.path.abspath(file) in cls.__dic

    @classmethod
    def OnMoveFile(cls,file,file_to):
        if cls.IsUsed(os.path.abspath(file)):
            cls.__dic[os.path.abspath(file)]()._Connect(os.path.abspath(file_to))
            cls._Remove(file)

    @classmethod
    def _FinalizeObject(cls,obj):
        obj()._Clear()
    @classmethod
    def _Append(cls,file,data):
        if cls.IsUsed(file):
            cls.__dic[os.path.abspath(file)]().Disconnect()
        cls.__dic[os.path.abspath(file)]=weakref.ref(data)
    @classmethod
    def _Remove(cls,file):
        del cls.__dic[os.path.abspath(file)]
    @classmethod
    def _GetData(cls,file):
        return cls.__dic[os.path.abspath(file)]()

class AutoSaved(object):
    def _load(self,file):
        with open(file,'r') as f:
            self.data=eval(f.read())
    def _save(self,file):
        with open(file,'w') as f:
            f.write(str(self.data))
    def _overrite(self,target):
        self.data=target.data
    def _init(self):
        pass

    def __new__(cls,file=None,BaseClass=None):
        if _DataManager.IsUsed(file):
            return _DataManager._GetData(file)
        else:
            if BaseClass is None:
                return super().__new__(cls)
            else:
                return BaseClass.__new__(cls)

    def __init__(self,file=None,BaseClass=None):
        try:
            self.__file
        except Exception:
            self.__loadFlg=True
            self.__file=file
            if BaseClass is not None:
                BaseClass.__init__(self)
            self._init()
            if file is not None:
                self.__Load(file)
            self.__finalizer=weakref.finalize(self,_DataManager._FinalizeObject,weakref.ref(self))
            self.__loadFlg=False
    def FileName(self):
        return self.__file
    def Name(self):
        if self.FileName() is None:
            return "untitled"
        else:
            nam,ext=os.path.splitext(os.path.basename(self.FileName()))
            return nam
    def __del__(self):
        if self.__finalizer.alive:
            self.__finalizer()
    def _Clear(self):
        self.Save()
        self.Disconnect()
    def _Connect(self,file):
        if file is None:
            return
        self.__file=os.path.abspath(file)
        _DataManager._Append(self.__file,self)
    def IsConnected(self):
        return self.__file is not None
    def Disconnect(self):
        if _DataManager.IsUsed(self.__file):
            _DataManager._Remove(self.__file)
        self.__file=None
    def __Load(self,file):
        if _DataManager.IsUsed(file):
            print('Error: This file is already loaded.\n')
        else:
            self._Connect(file)
            if os.path.exists(self.__file):
                self._load(self.__file)
    def Save(self,file=None):
        if _DataManager.IsUsed(file):
            return False
        self._Connect(file)
        if self.__file is not None:
            self._save(self.__file)
        return True
    def Overwrite(self,target):
        self.__loadFlg=True
        self._overwrite(target)
        self.__loadFlg=False
        self.Save()
    def __setattr__(self,key,value):
        super().__setattr__(key,value)
        if not self.__loadFlg and not key =='_AutoSaved__loadFlg':
            self.Save()

class Wave(AutoSaved):
    __waveModListener=[]

    @classmethod
    def AddWaveModificationListener(cls, listener):
        cls.__waveModListener.append(weakref.ref(listener))
    @classmethod
    def _EmitWaveModified(cls,wave):
        for l in cls.__waveModListener:
            if l() is not None:
                l().OnWaveModified(wave)
            else:
                cls.__waveModListener.remove(l)

    def __setattr__(self,key,value):
        if key=='x' or key=='y' or key=='z' or key=='data':
            super().__setattr__(key,np.array(value))
            if self._emitflg:
                Wave._EmitWaveModified(self)
        else:
            super().__setattr__(key,value)
    def __getattribute__(self,key):
        if key=='x' or key=='y' or key=='z':
            val=super().__getattribute__(key)
            if val.ndim==0:
                index=['x','y','z'].index(key)
                if self.data.ndim>index:
                    return np.arange(self.data.shape[index])
                else:
                    return val
            else:
                return val
        else:
            return super().__getattribute__(key)
    def _init(self):
        self._emitflg=False
        self.data=[0]
        self.x=self.y=self.z=None
        self.note=""
        self._emitflg=True
    def _load(self,file):
        tmp=np.load(file)
        self._emitflg=False
        self.data=tmp['data']
        self.x=tmp['x']
        self.y=tmp['y']
        self.z=tmp['z']
        self.note=tmp['note']
        self._emitflg=True
    def _save(self,file):
        np.savez(file, data=self.data, x=self.x, y=self.y, z=self.z,note=self.note)
    def _overwrite(self,target):
        self.data=target.data
        self.x=target.x
        self.y=target.y
        self.z=target.z
        self.note=target.note

    def slice(self,pos1,pos2,axis='x'):
        index=['x','y'].index(axis)
        size=pos2[index]-pos1[index]
        x,y=np.linspace(pos1[0], pos2[0], size), np.linspace(pos1[1], pos2[1], size)
        res=scipy.ndimage.map_coordinates(self.data, np.vstack((x,y)))
        w=Wave()
        w.data=res
        w.x=self.x[pos1[index]:pos2[index]]
        return w

class String(AutoSaved):
    def _init(self):
        self.data=""

    def __setattr__(self,key,value):
        if key=='data':
            super().__setattr__(key,str(value))
        else:
            super().__setattr__(key,value)

    def _load(self,file):
        with open(file,'r') as f:
            self.data=f.read()

class Variable(AutoSaved):
    def _init(self):
        self.data=0
class Dict(AutoSaved):
    def _init(self):
        self.data={}
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

class SizeAdjustableWindow(QMdiSubWindow):
    def __init__(self):
        super().__init__()
        #Mode
        #0 : Auto
        #1 : heightForWidth
        #2 : widthForHeight
        self.__mode=0
        self.__aspect=0
        self.setWidth(0)
        self.setHeight(0)
    def setWidth(self,val):
        if self.__mode==2:
            self.__mode=0
        if val==0:
            self.setMinimumWidth(85)
            self.setMaximumWidth(100000)
        else:
            self.setMinimumWidth(val)
            self.setMaximumWidth(val)
    def setHeight(self,val):
        if self.__mode==1:
            self.__mode=0
        if val==0:
            self.setMinimumHeight(85)
            self.setMaximumHeight(100000)
        else:
            self.setMinimumHeight(val)
            self.setMaximumHeight(val)
    def setHeightForWidth(self,val):
        self.__mode=1
        self.__aspect=val
    def setWidthForHeight(self,val):
        self.__mode=2
        self.__aspect=val
    def resizeEvent(self,event):
        self._resizeEvent(event.size())
        return super().resizeEvent(event)
    def _resizeEvent(self,size):
        if self.__mode==1:
            self.setMinimumHeight(size.width()*self.__aspect)
            self.setMaximumHeight(size.width()*self.__aspect)
        elif self.__mode==2:
            self.setMinimumWidth(size.height()*self.__aspect)
            self.setMaximumWidth(size.height()*self.__aspect)

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

class AutoSavedWindow(AttachableWindow, AutoSaved):
    __list=[]
    mdimain=None
    @classmethod
    def CloseAllWindows(cls):
        for g in cls.__list:
            g.close()
    @classmethod
    def _AddWindow(cls,win):
        cls.__list.append(win)
    @classmethod
    def _RemoveWindow(cls,win):
        cls.__list.remove(win)
    @classmethod
    def _Contains(cls,win):
        return win in cls.__list
    @classmethod
    def DisconnectedWindows(cls):
        res=[]
        for g in cls.__list:
            if not g.IsConnected():
                res.append(g)
        return res
    @classmethod
    def AllWindows(cls):
        return cls.__list

    def __new__(cls, file=None,title=None):
        return AutoSaved.__new__(cls,file,AttachableWindow)
    def __init__(self, file=None, title=None):
        AutoSaved.__init__(self,file,AttachableWindow)
        AutoSavedWindow._AddWindow(self)
        if title is not None:
            self.setWindowTitle(title)
        self.updateGeometry()
        self.show()
    def __setattr__(self,key,value):
        object.__setattr__(self,key,value)
    def closeEvent(self,event):
        if self.IsConnected() or self.isHidden():
            self.Save()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("This window is not saved. Do you really want to close it?")
            msg.setWindowTitle("Caution")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ok = msg.exec_()
            if ok==QMessageBox.Cancel:
                event.ignore()
                return
        AutoSavedWindow._RemoveWindow(self)
        self.Disconnect()
        event.accept()
        return AttachableWindow.closeEvent(self,event)
    def hide(self):
        sys.stderr.write('This window cannot be hidden.\n')
    def show(self):
        if AutoSavedWindow._Contains(self):
            super().show()
        else:
            sys.stderr.write('This window is already closed.\n')
__home=os.getcwd()
__CDChangeListener=[]
