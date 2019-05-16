import copy
from ExtendAnalysis import *
from dask.array.core import Array as DArray
import dask.array as da

class DaskWave(object):
    def __init__(self,wave,axes=None,chunks=64):
        if isinstance(wave,Wave):
            self.__fromWave(wave,axes,chunks)
        elif isinstance(wave,DArray):
            self.__fromda(wave,axes,chunks)
    def __fromWave(self,wave,axes,chunks):
        self.data=da.from_array(wave.data,chunks=chunks)
        if axes is None:
            self.axes=wave.axes
        else:
            self.axes=axes
    def toWave(self):
        w=Wave()
        w.data=self.data.compute()
        w.axes=self.axes
        return w
    def __fromda(self,wave,axes,chunks):
        self.data=wave
        self.axes=axes
    def shape(self):
        return self.data.shape
    def posToPoint(self,pos,axis):
        ax=self.axes[axis]
        if (ax == np.array(None)).all():
            return int(round(pos))
        x0=ax[0]
        x1=ax[len(ax)-1]
        dx=(x1-x0)/(len(ax)-1)
        return int(round((pos-x0)/dx))
    def sum(self,axis):
        data=self.data.sum(axis)
        axes=[]
        for i, ax in enumerate(self.axes):
            if not i == axis:
                axes.append(ax)
        return DaskWave(data,axes=axes)
    def __getitem__(self,key):
        if isinstance(key,tuple):
            data=self.data[key]
            axes=[]
            for s, ax in zip(key,self.axes):
                axes.append(ax[s])
            return DaskWave(data,axes=axes)
        else:
            super().__getitem__(key)

class controlledObjects(QObject):
    appended=pyqtSignal()
    removed=pyqtSignal()
    def __init__(self):
        super().__init__()
        self._objs=[]
        self._axis=[]
    def append(self,obj,axes):
        self._objs.append(obj)
        self._axis.append(axes)
        self.appended.emit()
    def remove(self,obj):
        if obj in self._objs:
            i=self._objs.index(obj)
            self._objs.pop(i)
            self._axis.pop(i)
            self.removed.emit()
    def removeAt(self,index):
        self.remove(self._objs[index])
    def getAxes(self,obj):
        i=self._objs.index(obj)
        return self._axis[i]
    def getObjectsAndAxes(self):
        return zip(self._objs,self._axis)
    def __len__(self):
        return len(self._objs)
    def __getitem__(self,index):
        return [self._objs[index],self._axis[index]]

class ExecutorList(controlledObjects):
    updated = pyqtSignal(tuple)
    def __init__(self):
        super().__init__()
    def append(self,obj):
        super().append(obj,obj.getAxes())
        obj.updated.connect(self.updated.emit)
    def remove(self,obj):
        obj.updated.disconnect()
        super().remove(obj)
    def enable(self,obj):
        pass
    def enableAt(self,index):
        self.enable(self._objs[index])
    def disable(self,obj):
        pass
    def disableAt(self,obj):
        self.disable(self._objs[index])
    def __exeList(self,wave):
        axes=[]
        for e in self._objs:
            axes.extend(e.getAxes())
        axes=list(set(axes))
        res=list(self._objs)
        for i in range(wave.data.ndim):
            if not i in axes:
                res.append(AllExecutor(i))
        return res
    def makeWave(self,wave,axes):
        tmp=wave
        offset=0
        for e in self.__exeList(wave):
            tmp, off = e.execute(tmp,offset,ignore=axes)
            offset += off
        if len(axes) == 2:
            if axes[0] > axes[1]:
                tmp.data=tmp.data.T
                t=tmp.axes[0]
                tmp.axes[0]=tmp.axes[1]
                tmp.axes[1]=t
        return tmp.toWave()
class AllExecutor(QObject):
    updated = pyqtSignal(tuple)
    def __init__(self,axis):
        super().__init__()
        self.axis=axis
    def getAxes(self):
        return [self.axis]
    def execute(self,wave,axis_offset,ignore=[]):
        if self.axis in ignore:
            return wave, 0
        else:
            return wave.sum(self.axis-axis_offset), 1
class RegionExecutor(QObject):
    updated = pyqtSignal(tuple)
    def __init__(self,axes,range=None):
        super().__init__()
        if isinstance(axes,int):
            self.axes=(axes,)
        else:
            self.axes=tuple(axes)
        if range is not None:
            self.setRange(range)
    def getAxes(self):
        return self.axes
    def setRange(self,range):
        self.range=[]
        if isinstance(range[0],list):
            for r in range:
                self.range.append(r)
        else:
            self.range.append(range)
        self.updated.emit(self.axes)
    def execute(self,wave,axis_offset,ignore=[]):
        off=0
        tmp = wave
        for i, r in zip(self.axes,self.range):
            if not i in ignore:
                sl = [slice(None)]*tmp.data.ndim
                sl[i-axis_offset-off] = slice(wave.posToPoint(r[0],i),wave.posToPoint(r[1],i))
                tmp = tmp[tuple(sl)].sum(i-axis_offset-off)
                off += 1
        return tmp, off
    def callback(self,region):
        self.setRange(region)
    def Name(self):
        return "Region"
class PointExecutor(QObject):
    updated = pyqtSignal(tuple)
    def __init__(self,axes,pos=None):
        super().__init__()
        if isinstance(axes,int):
            self.axes=(axes,)
        else:
            self.axes=axes
        if pos is not None:
            self.setPosition(pos)
    def getAxes(self):
        return self.axes
    def setPosition(self,pos):
        if isinstance(pos,float) or isinstance(pos,int):
            self.position=[pos]
        else:
            self.position=pos
        self.updated.emit(self.axes)
    def execute(self,wave,axis_offset,ignore=[]):
        off=0
        tmp = wave
        for i, p in zip(self.axes,self.position):
            if not i in ignore:
                sl = [slice(None)]*tmp.data.ndim
                sl[i-off] = wave.posToPoint(p,i)
                tmp = tmp[tuple(sl)]#.sum(i-axis_offset-off)
                off += 1
        return tmp, off
    def callback(self,pos):
        self.setPosition(pos)
    def Name(self):
        return "Point"
