from PyQt5 import QtCore
from PyQt5.QtWidgets import *

class __print_dummy(QtCore.QObject):
    print_new=QtCore.pyqtSignal(tuple)
    def __init__(self):
        super().__init__()
        self.print_new.connect(self.p)
    def p(self,args):
        print_orig(*args)

d=__print_dummy()

print_orig=print
def print(*args):
    id_orig=QApplication.instance().thread()
    id=QtCore.QThread.currentThread()
    if id==id_orig:
        print_orig(*args)
    else:
        d.print_new.emit(args)


class Tasks(QtCore.QObject):
    updated=QtCore.pyqtSignal()
    sequenceFinished=QtCore.pyqtSignal()
    singleFinished=QtCore.pyqtSignal()
    __list=[]
    def _exenext(self,obj):
        self.__list.remove(self.__list[0])
        if len(self.__list)==0:
            self.sequenceFinished.emit()
        else:
            i=self.__list[0][0]
            i.start()
        self.updated.emit()

    __num=0
    def sequence(self,func,*args,name=None,text=""):
        t=_thread(func,*args)
        t.finish.connect(self._exenext)
        if name is None:
            self.__num+=1
            name="single"+str(self.__num)
        self.__list.append([t,name,text])
        if len(self.__list)==1:
            t.start()
        self.updated.emit()


    __threadlist=[]
    __threadnum=0
    def single(self,func,*args,name=None,text=""):
        t=_thread(func,*args)
        t.finish.connect(self._singleFinished)
        if name is None:
            self.__threadnum+=1
            name="single"+str(self.__threadnum)
        self.__threadlist.append([t,name,text])
        t.start()
        self.updated.emit()

    def _singleFinished(self,obj):
        for i in range(len(self.__threadlist)):
            if self.__threadlist[i][0]==obj:
                self.__threadlist.remove(self.__threadlist[i])
                self.singleFinished.emit()
                self.updated.emit()
                return

    def getTasks(self):
        res=[]
        res.extend(self.__threadlist)
        res.extend(self.__list)
        return res
    def removeTask(self,thread):
        try:
            for i in range(len(self.__threadlist)):
                if self.__threadlist[i][0]==thread:
                    self.__threadlist.remove(self.__threadlist[i])
                    self.updated.emit()
                    return
            for j in range(len(self.__list)):
                if self.__list[j][0]==thread:
                    self.__list.remove(self.__list[j])
                    self.updated.emit()
                    return
        except:
            pass

class _worker(QtCore.QObject):
    def __init__(self,func,*args):
        super().__init__()
        self.f=func
        self.arg=args
    def run(self):
        try:
            res=self.f(*self.arg)
        except:
            import traceback
            print(traceback.format_exc())

class _thread(QtCore.QThread):
    finish=QtCore.pyqtSignal(QtCore.QThread)
    def __init__(self,func,*args):
        super().__init__()
        self.worker=_worker(func,*args)
    def run(self):
        self.worker.run()
        self.finish.emit(self)

tasks=Tasks()
