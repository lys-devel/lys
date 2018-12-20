from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from concurrent.futures import *

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
    def execute(self,dlist):
        self.futures=[]
        self.count=len(dlist)
        for d in dlist:
            f=self.pool.submit(d.func, *d.args)
            f.add_done_callback(self.callback)
            self.futures.append(f)
        tasks._list.append(self)
        tasks.update()
        if self.blocking:
            tasks.update()
            return self.getResult()
        else:
            return
    def getResult(self):
        res=[]
        (done, notdone)=wait(self.futures)
        for f in self.futures:
            res.append(f.result())
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
            return str(int(float((1-self.count/len(self.futures))*100)))+"%"
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
