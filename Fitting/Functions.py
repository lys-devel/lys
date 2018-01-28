from inspect import signature
import numpy as np
from scipy import ndimage

class function(object):
    def func(self,x,*p):
        return 0
    def nparam(self):
        s=signature(self.func)
        return len(s.parameters)-1
    def params(self):
        res=[]
        sig=signature(self.func)
        flg=False
        for key in sig.parameters.keys():
            if not flg:
                flg=True
            else:
                res.append(key)
        return res
class none(function):
    def func(self,x):
        return np.zeros((x.shape[0]))
class const(function):
    def func(self,x,value):
        return np.ones((x.shape[0]))*value
class linear(function):
    def func(self,x,a,b):
        return a*x+b

class step(function):
    def func(self,x,position,height):
        np.heaviside(x-position,0.5)*height
class GaussConvolved(function):
    def __init__(self, f):
        self.f=f
    def func(self,x,*p):
        res=self.f.func(x,*p[len(p)-2])
        res=ndimage.gaussian_filter(res, sigma=p[len(p)-1]/np.sqrt(8*np.ln(2)))
        return res
    def nparam(self):
        return self.f.nparam()+1
    def params(self):
        res=self.f.params()
        res.append('Resolution')
        return res
ListOfFunctions={"Const" : const(), "Linear" : linear(), 'Step' : step()}
def findFuncByInstance(instance):
    for key in ListOfFunctions.keys():
        if ListOfFunctions[key]==instance:
            return key
