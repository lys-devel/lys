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
    def submit(self,task,*args,**kwargs):
        p=_parallelExecutor(*args,**kwargs)
        return p._execute(task)
    def execute(self,task,*args,**kwargs):
        p=_parallelExecutor(*args,**kwargs)
        c=p._execute(task)
        return c.result()


class Callable(object):
    def __init__(self,submit,task):
        super().__init__()
        self.submit=submit
        self.task=task
        self.obj=None
        self._calls=[]
        self._children=self._callables()
        self.count=len(self._children)
        for c in self._children:
            c.addCallback(self._childFinished)
        if self.count==0:
            self._submit()
    def _callables(self):
        res=[]
        for arg in self.task.args:
            if isinstance(arg,Callable):
                res.append(arg)
        return res
    def _childFinished(self,res):
        self.count-=1
        if self.count==0:
            self._submit()
    def _submit(self):
        args=[]
        for arg in self.task.args:
            if isinstance(arg,Callable):
                args.append(arg.result())
            else:
                args.append(arg)
        self.obj=self.submit(self.task.func,*args)
        for c in self._calls:
            self.obj.add_done_callback(c)
    def addCallback(self,call):
        if self.obj is None:
            self._calls.append(call)
        else:
            self.obj.add_done_callback(call)
    def result(self):
        self._wait()
        return self.obj.result()
    def _wait(self):
        for c in self._children:
            c._wait()
        while self.obj is None:
            pass
        while not self.obj.done():
            pass
    def status(self):
        if self.obj is None:
            "Waiting"
        else:
            "Executing"
class CallableList(Callable):
    def __init__(self,callables):
        self._calls=[]
        self._children=callables
        self.count=len(self._children)
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
            for c in self._calls:
                c(self)
        tasks.update()
    def result(self):
        self._wait()
        return [t.result() for t in self._children]
    def _wait(self):
        for c in self._children:
            c._wait()
    def __iter__(self):
        self._i=0
        return self
    def __next__(self):
        if self._i==len(self._children):
            raise StopIteration
        self._i+=1
        return self._children[self._i-1]
    def status(self):
        if self.count==len(self._children):
            return "Waiting"
        else:
            return str(int(float(1-self.count/len(self._children))*100))+'%'

class _parallelExecutor(QObject):
    finished=pyqtSignal(object)
    _n=0
    @classmethod
    def _name(cls):
        cls._n+=1
        return "Task"+str(cls._n)
    def __init__(self,finished=None,type="Process",max_workers=None,name=None,explanation=""):
        super().__init__()
        if type=="Process":
            self.pool=ProcessPoolExecutor(max_workers=max_workers)
        elif type=="Thread":
            self.pool=ThreadPoolExecutor(max_workers=max_workers)
        if finished is not None:
            self.finished.connect(finished)
        if name is None:
            self.nam=_parallelExecutor._name()
        else:
            self.nam=name
        self.expl=explanation
        self.futures=[]
    def _execute(self,dlist):
        if hasattr(dlist, "__iter__"):
            self.obj=CallableList([Callable(self.pool.submit,d) for d in dlist])
        else:
            self.obj=Callable(self.pool.submit,dlist)
        self.obj.addCallback(self.callback)
        tasks._list.append(self)
        tasks.update()
        return self.obj
    def callback(self,res):
        self.finished.emit(res.result())
        tasks._list.remove(self)
        tasks.update()
    def status(self):
        return self.obj.status()
    def name(self):
        return self.nam
    def explanation(self):
        return self.expl

class task(object):
	def __init__(self,func,*args):
		self.func=func
		self.args=args

tasks=Tasks()
