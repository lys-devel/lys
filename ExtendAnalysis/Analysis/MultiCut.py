import copy
from ExtendAnalysis import *
from dask.array.core import Array as DArray
import dask.array as da

class DaskWave(object):
    def __init__(self,wave,axes=None,chunks="auto"):
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
        import copy
        w=Wave()
        res=self.data.compute()
        w.data=res
        w.axes=copy.copy(self.axes)
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
                if not isinstance(s,int):
                    if ax is None or (ax == np.array(None)).all():
                        axes.append(None)
                    else:
                        axes.append(ax[s])
            return DaskWave(data,axes=axes)
        else:
            super().__getitem__(key)

class controlledObjects(QObject):
    appended=pyqtSignal(object)
    removed=pyqtSignal(object)
    def __init__(self):
        super().__init__()
        self._objs=[]
        self._axis=[]
    def append(self,obj,axes):
        self._objs.append(obj)
        self._axis.append(axes)
        self.appended.emit(obj)
    def remove(self,obj):
        if obj in self._objs:
            i=self._objs.index(obj)
            self._objs.pop(i)
            self._axis.pop(i)
            self.removed.emit(obj)
            return i
        return None
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
        self._enabled=[]
        self._graphs=[]
    def graphRemoved(self,graph):
        for i, g in enumerate(self._graphs):
            if g == graph:
                self.removeAt(i)
    def append(self, obj, graph=None):
        super().append(obj,obj.getAxes())
        self._enabled.append(False)
        self._graphs.append(graph)
        obj.updated.connect(self.updated.emit)
        self.enable(obj)
    def remove(self,obj):
        obj.updated.disconnect()
        i = super().remove(obj)
        if i is not None:
            self._enabled.pop(i)
            self._graphs.pop(i)
        self.updated.emit(obj.getAxes())
        return i
    def enableAt(self,index):
        self.enable(self._objs[index])
    def enable(self,obj):
        i = self._objs.index(obj)
        self._enabled[i]=True
        if isinstance(obj,FreeLineExecutor):
            return
        for o in self._objs:
            if not o == obj:
                for ax1 in obj.getAxes():
                    for ax2 in o.getAxes():
                        if ax1 == ax2 and not isinstance(o,FreeLineExecutor):
                            self.disable(o)
        self.updated.emit(obj.getAxes())
    def setting(self,index):
        self._objs[index].setting()
    def disable(self,obj):
        i = self._objs.index(obj)
        self._enabled[i]=False
        self.updated.emit(obj.getAxes())
    def disableAt(self,index):
        self.disable(self._objs[index])
    def getFreeLines(self):
        res=[]
        for o in self._objs:
            if isinstance(o,FreeLineExecutor):
                res.append(o)
        return res
    def isEnabled(self,i):
        return self._enabled[i]
    def saveEnabledState(self):
        import copy
        self._saveEnabled=copy.deepcopy(self._enabled)
    def restoreEnabledState(self):
        for i, b in enumerate(self._saveEnabled):
            if b:
                self.enableAt(i)
            else:
                self.disableAt(i)
    def __exeList(self,wave):
        axes = []
        res = []
        for i, e in enumerate(self._objs):
            if self.isEnabled(i):
                if not isinstance(self._objs,FreeLineExecutor):
                    axes.extend(e.getAxes())
                    res.append(e)
        for i in range(wave.data.ndim):
            if not i in axes:
                res.append(AllExecutor(i))
        return res
    def __findFreeLineExecutor(self,id):
        for fl in self.getFreeLines():
            if fl.ID() == id:
                return fl
    def __ignoreList(self,axes):
        ignore=[]
        for ax in axes:
            if ax < 10000:
                ignore.append(ax)
            else:
                ignore.extend(self.__findFreeLineExecutor(ax).getAxes())
        return ignore
    def __applyFreeLines(self,wave,axes_orig,applied):
        for a in axes_orig:
            if a >= 10000:
                fl=self.__findFreeLineExecutor(a)
                axes = fl.getAxes()
                for i, ax in enumerate(axes):
                    for ax2 in applied:
                        if ax2 < ax:
                            axes[i] -= 1
                fl.execute(wave,axes)
    def makeWave(self,wave,axes):
        tmp=wave
        offset=0
        applied=[]
        for e in self.__exeList(wave):
            if not isinstance(e,FreeLineExecutor):
                tmp, axs = e.execute(tmp,offset,ignore=self.__ignoreList(axes))
                offset += len(axs)
                applied.extend(axs)
        res=tmp.toWave()
        self.__applyFreeLines(res,axes,applied)
        if len(axes) == 2 and axes[0] < 10000:
            if axes[0] > axes[1] or axes[1] >= 10000:
                res.data=res.data.T
                t=res.axes[0]
                res.axes[0]=res.axes[1]
                res.axes[1]=t
        return res
class AllExecutor(QObject):
    updated = pyqtSignal(tuple)
    def __init__(self,axis):
        super().__init__()
        self.axis=axis
    def getAxes(self):
        return [self.axis]
    def execute(self,wave,axis_offset,ignore=[]):
        if self.axis in ignore:
            return wave, []
        else:
            return wave.sum(self.axis-axis_offset), [self.axis]
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
        axes = []
        for i, r in zip(self.axes,self.range):
            if not i in ignore:
                sl = [slice(None)]*tmp.data.ndim
                sl[i-axis_offset-off] = slice(wave.posToPoint(r[0],i),wave.posToPoint(r[1],i))
                tmp = tmp[tuple(sl)].sum(i-axis_offset-off)
                off += 1
                axes.append(i)
        return tmp, axes
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
        axes = []
        for i, p in zip(self.axes,self.position):
            if not i in ignore:
                sl = [slice(None)]*tmp.data.ndim
                sl[i-off] = wave.posToPoint(p,i)
                tmp = tmp[tuple(sl)]#.sum(i-axis_offset-off)
                off += 1
                axes.append(i)
        return tmp, axes
    def callback(self,pos):
        self.setPosition(pos)
    def Name(self):
        return "Point"
class FreeLineExecutor(QObject):
    _id=10000
    updated = pyqtSignal(tuple)
    def __init__(self,axes,pos=None):
        super().__init__()
        self.axes=axes
        self.id = FreeLineExecutor._id
        FreeLineExecutor._id +=1
        self.width = 1
        if pos is not None:
            self.setPosition(pos)
    def getAxes(self):
        return self.axes
    def setPosition(self,pos):
        self.position=pos
        self.updated.emit((self.id,))
    def setting(self):
        val, res = QInputDialog.getInt(None,"Setting for free line","width")
        if res:
            self.setWidth(val)
        self.updated.emit((self.id,))
    def setWidth(self,w):
        self.width = w
    def execute(self,wave,axes):
        import copy
        width = self.width
        pos1 = (wave.posToPoint(self.position[0][0],axes[0]),wave.posToPoint(self.position[1][0],axes[0]))
        pos2 = (wave.posToPoint(self.position[0][1],axes[1]),wave.posToPoint(self.position[1][1],axes[1]))
        dx=(pos2[0]-pos1[0])
        dy=(pos2[1]-pos1[1])
        size=int(np.sqrt(dx*dx+dy*dy)+1)
        nor=np.sqrt(dx*dx+dy*dy)
        dx, dy = dy/nor, -dx/nor
        coords_array=[]
        coords_shape=[]
        for ax in range(wave.data.ndim):
            if ax in axes:
                if ax == axes[0]:
                    coords_shape.append(size)
                    coords_array.append("x")
                else:
                    coords_array.append("y")
            else:
                coords_shape.append(wave.data.shape[ax])
                coords_array.append(np.linspace(0,wave.data.shape[ax]-1,wave.data.shape[ax]))
        replacedAxis = min(*axes)
        res = np.zeros(tuple(coords_shape))
        for j in range(1-width,width,2):
            coords = []
            x, y = np.linspace(pos1[0], pos2[0], size) + dx*(j*0.5), np.linspace(pos1[1], pos2[1], size) + dy*(j*0.5)
            offset = 0
            for d1, ar in enumerate(coords_array):
                shape = copy.copy(coords_shape)
                if isinstance(ar,str):
                    shape.pop(replacedAxis)
                    ord = list(range(len(coords_shape)-1))
                    ord.insert(replacedAxis,len(coords_shape)-1)
                    if ar == "x":
                        tmp = np.tile(x,tuple([*shape,1]))
                    elif ar == "y":
                        tmp = np.tile(y,tuple([*shape,1]))
                        offset = 1
                    tmp=tmp.transpose(tuple(ord))
                else:
                    shape.pop(d1 - offset)
                    ord = list(range(len(coords_shape)-1))
                    ord.insert(d1 - offset,len(coords_shape)-1)
                    tmp = np.tile(ar,tuple([*shape,1]))
                    tmp=tmp.transpose(tuple(ord))
                coords.append(tmp)
            res += scipy.ndimage.map_coordinates(wave.data, coords, order = 1)
        axis1=wave.getAxis(axes[0])
        if axis1 is None:
            axis1=list(range(wave.data.shape[axes[0]]))
        axis2=wave.getAxis(axes[1])
        if axis2 is None:
            axis2=list(range(wave.data.shape[axes[1]]))
        dx=abs(axis1[pos1[0]]-axis1[pos2[0]])
        dy=abs(axis2[pos1[1]]-axis2[pos2[1]])
        d=np.sqrt(dx*dx+dy*dy)
        axisData=np.linspace(0,d,size)
        wave.axes[replacedAxis]=axisData
        wave.axes=np.delete(wave.axes,max(*axes),0)
        wave.data=res
        return wave
    def callback(self,pos):
        self.setPosition(pos)
    def Name(self):
        return "Line"+str(self.id-10000)+" (width = " + str(self.width) + ")"
    def ID(self):
        return self.id
