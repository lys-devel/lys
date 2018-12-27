from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from concurrent.futures import *
import time,os,threading,multiprocessing
from loky import get_reusable_executor

class Tasks(QObject):
    updated=pyqtSignal()
    _list=[]
    timeInt=0
    def getTasks(self):
        return self._list
    def update(self):
        self.updated.emit()
    def submit(self,task,*args,**kwargs):
        p=_parallelExecutor(*args,**kwargs)
        return p._execute(task)
    def execute(self,task,*args,**kwargs):
        p=_parallelExecutor(*args,**kwargs)
        c=p._execute(task)
        return c.result()
    def zip(self,tasks):
        return CallableList(tasks)

class Callable(object):
    _i=0
    def __init__(self,submit,task,wait=None):
        super().__init__()
        self.submit=submit
        self.task=task
        self.wait=wait
        self.obj=None
        self.done=False
        self.res=None
        self._calls=[]
        self._children=self._callables()
        self.count=len(self._children)
        for c in self._children:
            c.addCallback(self._childFinished)
    def _callables(self):
        res=[]
        for arg in self.task.args:
            if isinstance(arg,Callable):
                res.append(arg)
        for arg in self.task.kwargs:
            if isinstance(arg,Callable):
                res.append(arg)
        return res
    def _childFinished(self,res):
        self.count-=1
        if self.count==0:
            #print("Callable:childfinished.",os.getpid(),threading.get_ident())
            self._submit()
    def _submitIfPossible(self):
        if len(self._children)==0:
            self._submit()
    def _submit(self):
        Callable._i+=1
        args=[]
        #if self.wait is not None:
        #    self.wait.result()
        for arg in self.task.args:
            if isinstance(arg,Callable):
                args.append(arg.result())
            else:
                args.append(arg)
        kwargs={}
        for key,kwarg in self.task.kwargs.items():
            if isinstance(kwarg,Callable):
                kwargs[key]=kwarg.result()
            else:
                kwargs[key]=kwarg
        #print("submit",Callable._i,os.getpid(),threading.get_ident(),self.task.func)
        self.obj=self.submit(self.task.func,*args,**kwargs)
        for c in self._calls:
            self.obj.add_done_callback(c)
    def addCallback(self,call):
        if self.obj is None:
            self._calls.append(call)
        else:
            self.obj.add_done_callback(call)
    def result(self):
        #print("Callable.result")
        if self.res is None:
            self._wait()
            self.res=self.obj.result(0.01)
        return self.res
    def _wait(self):
        if self.done: return
        for c in self._children:
            c._wait()
        while self.obj is None:
            pass
        wait([self.obj])
        #while not self.obj.done():
        #    pass
        self.done=True
    def status(self):
        if self.obj is None:
            "Waiting"
        else:
            "Executing"
class CallableList(Callable):
    def __init__(self,callables):
        #print("callable list __init__")
        self._calls=[]
        self._children=callables
        self.count=len(self._children)
        self.done=False
        self.res=None
        for c in self._children:
            c.addCallback(self._childFinished)
    def addCallback(self,call):
        if self.count==0:
            call(self)
        else:
            self._calls.append(call)
    def _childFinished(self,res):
        self.count-=1
        if self.count==0:
            #print("Callablelist. children finished.")
            for c in self._calls:
                c(self)
        tasks.update()
    def result(self):
        #print("Callablelist.result")
        if self.res is None:
            self._wait()
            self.res=[t.result() for t in self._children]
        #print("Callablelist.result finished")
        return self.res
    def _submitIfPossible(self):
        for c in self._children:
            c._submitIfPossible()
    def _wait(self):
        if self.done: return
        for c in self._children:
            c._wait()
        self.done=True
    def __iter__(self):
        self._i=0
        return self
    def __next__(self):
        if self._i==len(self._children):
            raise StopIteration
        self._i+=1
        return self._children[self._i-1]
    def __len__(self):
        return len(self._children)
    def status(self):
        if self.count==len(self._children):
            return "Waiting"
        else:
            return str(int(float(1-self.count/len(self._children))*100))+'%'
"""
class SingleExecutor(object):
    def submit(self,func,*args):
        self.res=func(*args)
        return self
    def add_done_callback(self,c):
        c(self)
    def result(self):
        return self.res
    def done(self):
        return True
"""
class _parallelExecutor(QObject):
    _thread=ThreadPoolExecutor()
    _process=get_reusable_executor()
    _lock1=multiprocessing.Manager().Lock()
    _lock2=threading.Lock()
    finished=pyqtSignal(object)
    _n=0
    @classmethod
    def _name(cls):
        cls._n+=1
        return "Task"+str(cls._n)
    def __init__(self,finished=None,type="Thread",waitTask=None,name=None,explanation=""):
        super().__init__()
        if type=="Process":
            #self.pool=ProcessPoolExecutor()#
            self.pool=_parallelExecutor._process
        elif type=="Thread":
            #self.pool=ThreadPoolExecutor()
            self.pool=_parallelExecutor._thread
        if finished is not None:
            self.finished.connect(finished)
        if name is None:
            self.nam=_parallelExecutor._name()
        else:
            self.nam=name
        self.expl=explanation
        self.futures=[]
        self.wait=waitTask
    def _createCallables(self,submit,d):
        if hasattr(d,"__iter__"):
            res=CallableList([self._createCallables(submit,item) for item in d])
        else:
            res=Callable(submit,d,wait=self.wait)
        return res
    def _execute(self,dlist):
        self.obj=None
        tasks._list.append(self)
        #print("exe.start",os.getpid(),threading.get_ident())
        self.obj=self._createCallables(self._submit,dlist)
        self.obj._submitIfPossible()
        self.obj.addCallback(self.callback)
        tasks.update()
        return self.obj
    def _submit(self,*args,**kwargs):
        #with _parallelExecutor._lock1:
        #    with _parallelExecutor._lock2:
        res=self.pool.submit(*args,**kwargs)
        return res
    def callback(self,res):
        self.finished.emit(res)
        del self.pool
        tasks._list.remove(self)
        tasks.update()
    def status(self):
        if self.obj is None:
            return "Waiting"
        return self.obj.status()
    def name(self):
        return self.nam
    def explanation(self):
        return self.expl

class task(object):
    def __init__(self,func,*args,**kwargs):
        self.func=func
        self.args=args
        self.kwargs=kwargs

tasks=Tasks()
