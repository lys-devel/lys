import numpy as np
import scipy
from scipy import signal
from scipy.ndimage import filters
from scipy.ndimage.interpolation import rotate
import cv2

from dask_image import ndfilters as dfilters
from dask.array import apply_along_axis, einsum, fft, absolute

from ExtendAnalysis import Wave, tasks, task
from .MultiCut import DaskWave

class FilterInterface(object):
    def execute(self,wave,**kwargs):
        if isinstance(wave,Wave) or isinstance(wave,DaskWave) or isinstance(wave,np.array):
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
        self._kernel = [int((k+1)/2) for k in kernel]
    def _execute(self,wave,**kwargs):
        if isinstance(wave, Wave):
            wave.data = filters.median_filter(wave.data,size=self._kernel)
            return wave
        if isinstance(wave, DaskWave):
            wave.data = dfilters.median_filter(wave.data,size=self._kernel)
            return wave
        return filters.median_filter(wave,size=self._kernel)
    def getKernel(self):
        return [int(2*k-1) for k in self._kernel]
class AverageFilter(FilterInterface):
    def __init__(self,kernel):
        self._kernel=[int((k+1)/2) for k in kernel]
    def _execute(self,wave,**kwargs):
        if isinstance(wave, Wave):
            wave.data = filters.uniform_filter(wave.data,size=self._kernel)
            return wave
        if isinstance(wave, DaskWave):
            wave.data = dfilters.uniform_filter(wave.data,size=self._kernel)
            return wave
        return filters.uniform_filter(wave,size=self._kernel)
class GaussianFilter(FilterInterface):
    def __init__(self,kernel):
        self._kernel=kernel
    def _execute(self,wave,**kwargs):
        if isinstance(wave, Wave):
            wave.data = filters.gaussian_filter(wave.data,sigma=self._kernel)
            return wave
        if isinstance(wave, DaskWave):
            wave.data = dfilters.gaussian_filter(wave.data,sigma=self._kernel)
            return wave
        return filters.gaussian_filter(wave,sigma=self._kernel)
class BilateralFilter(FilterInterface):
    def __init__(self,kernel,s_color,s_space):
        self._kernel=kernel
        self._sc=s_color
        self._ss=s_space
    def _execute(self,wave,**kwargs):
        wave.data=cv2.bilateralFilter(np.array(wave.data,dtype=np.float32),self._kernel,self._sc,self._ss)

class ConvolutionFilter(FilterInterface):
    def __init__(self,axes):
        self._axes=axes
    def makeCore(self,dim):
        core=np.zeros([3 for i in range(dim)])
        core[tuple([1 for i in range(dim)])]=1
        return core
    def _getKernel(self,core, axis):
        raise NotImplementedError()
    def _kernel(self,wave,axis):
        core = self.makeCore(self._getDim(wave))
        return self._getKernel(core,axis)
    def _getDim(self,wave):
        if isinstance(wave, np.ndarray):
            return wave.ndim
        else:
            return wave.data.ndim
    def _execute(self,wave,**kwargs):
        for ax in self._axes:
            kernel=self._kernel(wave,ax)
            if isinstance(wave, Wave):
                wave.data = filters.convolve(wave.data,kernel)
            if isinstance(wave, DaskWave):
                wave.data = dfilters.convolve(wave.data,kernel)
            else:
                wave=filters.convolve(wave,kernel)
        return wave
class PrewittFilter(ConvolutionFilter):
    def _getKernel(self,core, axis):
        return filters.prewitt(core,axis = axis)
class SobelFilter(ConvolutionFilter):
    def _getKernel(self,core, axis):
        return filters.sobel(core,axis = axis)
class LaplacianFilter(ConvolutionFilter):
    def _getKernel(self,core, axis):
        res=np.array(core)
        for ax in self._axes:
            res += filters.convolve1d(core,[1,-2,1],axis=ax)
        res[tuple([1 for i in range(core.ndim)])]-=1
        return res
    def _execute(self,wave,**kwargs):
        kernel=self._kernel(wave,None)
        if isinstance(wave, Wave):
            wave.data = filters.convolve(wave.data,kernel)
        if isinstance(wave, DaskWave):
            wave.data = dfilters.convolve(wave.data,kernel)
        else:
            wave=filters.convolve(wave,kernel)
        return wave
class SharpenFilter(LaplacianFilter):
    def _getKernel(self,core, axis):
        res=super()._getKernel(core,axis)
        res[tuple([1 for i in range(core.ndim)])]-=1
        return res

def _filt(wave,axes,b,a):
    if isinstance(wave, Wave):
        wave.data=np.array(wave.data,dtype=np.float32)
        for i in axes:
            wave.data=signal.filtfilt(b,a,wave.data,axis=i)
    if isinstance(wave, DaskWave):
        for i in axes:
            wave.data=apply_along_axis(_filts,i,wave.data,b=b,a=a)
    else:
            wave=signal.filtfilt(b,a,wave,axis=i)
    return wave
def _filts(x,b,a):
	if x.shape[0] != 1:
		return signal.filtfilt(b,a,x)
	else:
		return np.array([0])#signal.filtfilt(b,a,x)
class LowPassFilter(FilterInterface):
    def __init__(self,order,cutoff,axes):
        self._b, self._a=signal.butter(order,cutoff)
        self._axes=axes
    def _execute(self,wave,**kwargs):
        return _filt(wave,self._axes,self._b,self._a)
class HighPassFilter(FilterInterface):
    def __init__(self,order,cutoff,axes):
        self._b, self._a=signal.butter(order,cutoff,btype='highpass')
        self._axes=axes
    def _execute(self,wave,**kwargs):
        return _filt(wave,self._axes,self._b,self._a)
class BandPassFilter(FilterInterface):
    def __init__(self,order,cutoff,axes):
        self._b, self._a=signal.butter(order,cutoff,btype='bandpass')
        self._axes=axes
    def _execute(self,wave,**kwargs):
        return _filt(wave,self._axes,self._b,self._a)
class BandStopFilter(FilterInterface):
    def __init__(self,order,cutoff,axes):
        self._b, self._a=signal.butter(order,cutoff,btype='bandstop')
        self._axes=axes
    def _execute(self,wave,**kwargs):
        return _filt(wave,self._axes,self._b,self._a)

class FourierFilter(FilterInterface):
    def __init__(self,axes,type="forward"):
        self.type=type
        self.axes=axes
    def _execute(self,wave,**kwargs):
        for d in self.axes:
            if isinstance(wave, Wave):
                if type == "forward":
                    wave.data = np.fft.fftn(wave.data,axes=self.axes)
                else:
                    wave.data = np.fft.ifftn(wave.data,axes=self.axes)
            if isinstance(wave, DaskWave):
                wave.data = absolute(fft.fftn(wave.data,axes=self.axes))
            else:
                wave.data = absolute(fft.ifftn(wave.data,axes=self.axes))
        return wave

class NormalizeFilter(FilterInterface):
    def _makeSlice(self):
        sl = []
        for i, r in enumerate(self._range):
            if (r[0] == 0 and r[1] == 0) or self._axis == i:
                sl.append(slice(None))
            else:
                sl.append(slice(*r))
        return tuple(sl)
    def __init__(self, range, axis):
        self._range=range
        self._axis = axis
    def _execute(self,wave,**kwargs):
        axes = list(range(wave.data.ndim))
        if self._axis == -1:
            wave.data=wave.data/wave.data[self._makeSlice()].mean()
        else:
            letters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n"]
            axes.remove(self._axis)
            nor = 1 / wave.data[self._makeSlice()].mean(axis = axes)
            subscripts = ""
            for i in range(wave.data.ndim):
                subscripts += letters[i]
            subscripts = subscripts+"," + letters[self._axis] + "->"+subscripts
            wave.data = einsum(subscripts,wave.data,nor)

class SelectRegionFilter(FilterInterface):
    def __init__(self, range):
        self._range=range
    def _execute(self,wave,**kwargs):
        sl = []
        for r in self._range:
            if r[0] == 0 and r[1] == 0:
                sl.append(slice(None))
            else:
                sl.append(slice(*r))
        key=tuple(sl)
        wave.data=wave.data[key]
        wave.axes=[ax[s] for s, ax in zip(key,wave.axes)]
        return wave

"""
class SymmetrizationFilter(FilterInterface):
    #position=(x,y)
    def __init__(self,position,angle):
        self._pos=position
        self._ang=angle
    def _execute(self,wave,**kwargs):
        rotated=rotate(wave.data,self._ang)
        p_orig = np.array([pos[0]-(wave.data.shape[1]-1)/2,pos[1]-(wave.data.shape[0]-1)/2])
        c_rot = np.array([rotated.shape[0]-1)/2, (rotated.shape[1]-1)/2])
        t=self._ang/180*np.pi
        R=np.array([[np.cos(t),-np.sin(t)],[np.sin(t),np.cos(t)]])
        p_rot=c_rot+R*p_orig
        w=Wave()
        w.data=rotated
        return w
"""
class Filters(object):
    def __init__(self,filters):
        self._filters=[]
        self._filters.extend(filters)
    def execute(self,wave,**kwargs):
        for f in self._filters:
            f.execute(wave,**kwargs)
    def insert(self,index,obj):
        self._filters.insert(index,obj)
    def getFilters(self):
        return self._filters
