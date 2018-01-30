from inspect import signature
import numpy as np
from scipy import ndimage
from collections import OrderedDict

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
        return np.heaviside(x-position,0.5)*height
class cos(function):
    def func(self,x,position,height,frequency,phase):
        return np.cos(frequency*(x-position)+phase)*height
class exp(function):
    def func(self,x,position,height,a):
        return np.exp(a*(x-position))*height
class doubleExp(function):
    def func(self,x,position,height,a,b):
        return height*np.heaviside(x-position,0.5)*(1-np.exp(-((x-position)/a)**2))*np.exp(-(x-position)/b)
class relaxOscillation(function):
    def func(self,x,position,height,frequency,phase,offset,relax):
        return height*np.heaviside(x-position,0.5)*np.exp(-(x-position)/relax)*(offset+np.cos(frequency*(x-position)+phase*np.pi/180))
class GaussConvolved(function):
    def __init__(self, f):
        self.f=f
    def func(self,x,*p):
        res=self.f.func(x,*p[:len(p)-1])
        res=ndimage.gaussian_filter(res, sigma=p[len(p)-1]/np.sqrt(8*np.log(2)))
        return res
    def nparam(self):
        return self.f.nparam()+1
    def params(self):
        res=self.f.params()
        res.append('Resolution')
        return res
ListOfFunctions=OrderedDict()
ListOfFunctions["Const"]=const()
ListOfFunctions["Linear"]=linear()
ListOfFunctions["Step"]=step()
ListOfFunctions["Cos"]=cos()
ListOfFunctions["Exp"]=exp()
ListOfFunctions["DoubleExp"]=doubleExp()
ListOfFunctions["relaxOsci"]=relaxOscillation()
ListOfFunctions["Error"]=GaussConvolved(step())
def findFuncByInstance(instance):
    for key in ListOfFunctions.keys():
        if ListOfFunctions[key]==instance:
            return key
