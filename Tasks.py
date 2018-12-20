from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from concurrent.futures import *
import time

class Tasks(QObject):
    updated=pyqtSignal()
    _list=[]
    def getTasks(self):
        return self._list
    def update(self):
        self.updated.emit()



class parallelExecutor(object):
    _n=0
    @classmethod
    def _name(cls):
        cls._n+=1
        return "Task"+str(cls._n)
    class JobCallback(object):
        def __init__(self,submit,func,args1,future,args2):
            self.submit=submit
            self.f=func
            self.a1=args1
            self.a2=args2
            self.nextcall=None
            future.add_done_callback(self.callback)
        def callback(self,res):
            self.future=self.submit(self.f,self,*self.a1,res.result(),*self.a2)
            if self.nextcall is not None:
                self.nextcall(self)
        def add_done_callback(self,func):
            self.nextcall=func
        def result(self):
            return self.future
    def __init__(self,blocking=True,finished=None,type="Process",max_workers=None,name=None,explanation=""):
        if type=="Process":
            self.pool=ProcessPoolExecutor(max_workers=max_workers)
        elif type=="Thread":
            self.pool=ThreadPoolExecutor(max_workers=max_workers)
        self.blocking=blocking
        self.finished=finished
        if name is None:
            self.nam=parallelExecutor._name()
        else:
            self.nam=name
        self.expl=explanation
        self.futures=[]

    def submit(self, func, call, *args):
        if call is not None:
            self.futures.remove(call)
        for i,arg in enumerate(args):
            if isinstance(arg,Future) or isinstance(arg,self.JobCallback):
                f=self.JobCallback(self.submit,func,args[:i-1],args[i],args[i+1:])
                self.futures.append(f)
                return f
        f=self.pool.submit(func,*args)
        f.add_done_callback(self.callback)
        self.futures.append(f)
        return f

    def execute(self,dlist):
        if hasattr(dlist, "__iter__"):
            self.count_max=self.count=len(dlist)
            for d in dlist:
                self.submit(d.func, None, *d.args)
        else:
            self.count=self.count_max=1
            self.submit(dlist.func, None, *dlist.args)
        tasks._list.append(self)
        tasks.update()
        if self.blocking:
            return self.getResult()
        else:
            if self.count_max==1:
                return self.futures[0]
            else:
                return self.futures
    def getResult(self):
        res=[]
        (done, notdone)=wait(self.futures)
        for f in self.futures:
            res.append(f.result())
        tasks.update()
        if self.count_max==1:
            return res[0]
        else:
            return res
    def callback(self,res):
        self.count-=1
        if self.count==0:
            if self.finished is not None:
                self.finished(self.getResult())
            tasks._list.remove(self)
        tasks.update()
    def status(self):
        if len(self.futures)==self.count:
            return "Waiting"
        else:
            return str(int(float((1-self.count/self.count_max)*100)))+"%"
    def name(self):
        return self.nam
    def explanation(self):
        return self.expl

def Parallel(*args,**kwargs):
	obj=parallelExecutor(*args,**kwargs)
	return obj.execute

def delayed(func):
	obj=_delayedFunc(func)
	return obj.setArgs

class _delayedFunc(object):
	def __init__(self,func):
		self.func=func
	def setArgs(self,*args):
		self.args=args
		return self

tasks=Tasks()
