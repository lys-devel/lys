import numpy as np
import scipy
from scipy import signal
import cv2
from ExtendAnalysis import Wave

class FilterInterface(object):
    def execute(self,wave,**kwargs):
        if isinstance(wave,Wave):
            self._execute(wave,**kwargs)
        if hasattr(wave, "__iter__"):
            for w in wave:
                self.execute(w,**kwargs)
    def _execute(self,wave,**kwargs):
        pass

class ShiftFilter(FilterInterface):
    def __init__(self,shift=None):
        self._s=shift
    def _execute(self,wave,shift=None,**kwargs):
        if shift is None:
            wave.data=(scipy.ndimage.interpolation.shift(np.array(wave.data,dtype=np.float32),self._s, cval=0))
        else:
            wave.data=(scipy.ndimage.interpolation.shift(np.array(wave.data,dtype=np.float32),shift, cval=0))

class MedianFilter(FilterInterface):
    def __init__(self,kernel):
        self._kernel=kernel
    def _execute(self,wave,**kwargs):
        wave.data=signal.medfilt(np.array(wave.data,dtype=np.float32),self._kernel)
class AverageFilter(FilterInterface):
    def __init__(self,kernel):
        self._kernel=kernel
    def _execute(self,wave,**kwargs):
        kernel=np.ones((self._kernel,self._kernel))/(self._kernel*self._kernel)
        wave.data=cv2.filter2D(np.array(wave.data,dtype=np.float32),-1,kernel)
class GaussianFilter(FilterInterface):
    def __init__(self,kernel):
        self._kernel=kernel
    def _execute(self,wave,**kwargs):
        kernel=cv2.getGaussianKernel(self._kernel,0)
        wave.data=cv2.filter2D(np.array(wave.data,dtype=np.float32),-1,kernel)
class BilateralFilter(FilterInterface):
    def __init__(self,kernel,s_color,s_space):
        self._kernel=kernel
        self._sc=s_color
        self._ss=s_space
    def _execute(self,wave,**kwargs):
        wave.data=cv2.bilateralFilter(np.array(wave.data,dtype=np.float32),self._kernel,self._sc,self._ss)

class PrewittFilter(FilterInterface):
    def __init__(self,type='x+y'):
        self._type=type
    def _execute(self,wave,**kwargs):
        kernel=np.array([[-1,0,1],[-1,0,1],[-1,0,1]])
        if self._type=='x':
            wave.data=cv2.filter2D(np.array(wave.data,dtype=np.float32),-1,kernel)
        if self._type=='y':
            wave.data=cv2.filter2D(np.array(wave.data,dtype=np.float32),-1,kernel.T)
        if self._type=='x+y':
            wave.data=cv2.filter2D(np.array(wave.data,dtype=np.float32),-1,kernel+kernel.T)
class SobelFilter(FilterInterface):
    def __init__(self,type='x+y'):
        self._type=type
    def _execute(self,wave,**kwargs):
        kernel=np.array([[-1,0,1],[-2,0,2],[-1,0,1]])
        if self._type=='x':
            wave.data=cv2.filter2D(np.array(wave.data,dtype=np.float32),-1,kernel)
        if self._type=='y':
            wave.data=cv2.filter2D(np.array(wave.data,dtype=np.float32),-1,kernel.T)
        if self._type=='x+y':
            wave.data=cv2.filter2D(np.array(wave.data,dtype=np.float32),-1,kernel+kernel.T)
class LaplacianFilter(FilterInterface):
    def _execute(self,wave,**kwargs):
        kernel=np.array([[-1,-1,-1],[-1,8,-1],[-1,-1,-1]])
        wave.data=cv2.filter2D(np.array(wave.data,dtype=np.float32),-1,kernel)
class SharpenFilter(FilterInterface):
    def _execute(self,wave,**kwargs):
        kernel=np.array([[-1,-1,-1],[-1,9,-1],[-1,-1,-1]])
        wave.data=cv2.filter2D(np.array(wave.data,dtype=np.float32),-1,kernel)

def _filt(data,*args):
    res=np.array(data,dtype=np.float32)
    for i in range(0,data.ndim):
        res=signal.filtfilt(*args,res,axis=i)
    return res
class LowPassFilter(FilterInterface):
    def __init__(self,order,cutoff):
        self._b, self._a=signal.butter(order,cutoff)
    def _execute(self,wave,**kwargs):
        wave.data=_filt(wave.data,self._b,self._a)
class HighPassFilter(FilterInterface):
    def __init__(self,order,cutoff):
        self._b, self._a=signal.butter(order,cutoff,btype='highpass')
    def _execute(self,wave,**kwargs):
        wave.data=_filt(wave.data,self._b,self._a)
class BandPassFilter(FilterInterface):
    def __init__(self,order,cutoff):
        self._b, self._a=signal.butter(order,cutoff,btype='bandpass')
    def _execute(self,wave,**kwargs):
        wave.data=_filt(wave.data,self._b,self._a)
class BandStopFilter(FilterInterface):
    def __init__(self,order,cutoff):
        self._b, self._a=signal.butter(order,cutoff,btype='bandstop')
    def _execute(self,wave,**kwargs):
        wave.data=_filt(wave.data,self._b,self._a)

class NormalizeFilter(FilterInterface):
    def _normalize(self,data,r):
        print(r)
        if not r[0]==0 and r[1]==0 and r[2]==0 and r[3]==0:
            data=data/np.average(data[r[2]:r[3],r[0]:r[1]])
        else:
            data=data/np.average(data)
        return data
    def __init__(self, range):
        self._range=range
    def _execute(self,wave,**kwargs):
        wave.data=self._normalize(np.array(wave.data,dtype=np.float32),self._range)

class SelectRegionFilter(FilterInterface):
    def _selrange(self,data,r):
        if r[0]==0 and r[1]==0 and r[2]==0 and r[3]==0:
            return data
        return data[r[2]:r[3],r[0]:r[1]]
    def __init__(self, range):
        self._range=range
    def _execute(self,wave,**kwargs):
        r=self._range
        wave.x=np.array(wave.x)[r[0]:r[1]]
        wave.y=np.array(wave.y)[r[2]:r[3]]
        wave.data=self._selrange(wave.data,self._range)

class Filters(object):
    def __init__(self,filters):
        self._filters=[]
        self._filters.extend(filters)
    def execute(self,wave,**kwargs):
        for f in self._filters:
            f.execute(wave,**kwargs)
    def insert(self,index,obj):
        self._filters.insert(index,obj)
