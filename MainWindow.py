from PyQt5.QtWidgets import *
from .ExtendShell import ExtendShell
from .GraphWindow import AutoSavedWindow, PreviewWindow, ExtendMdiSubWindow
from .ExtendType import home
from collections import OrderedDict

class MainWindow(QMainWindow):
    _actions=OrderedDict(File={"Exit":exit})
    _instance=None
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Analysis Program Lys')
        MainWindow._instance=self
        self.area=QMdiArea()
        self.setCentralWidget(self.area)
        ExtendMdiSubWindow.mdimain=self.area
        shell=ExtendShell()
        self.com=shell.CommandWindow()
        self.area.addSubWindow(self.com)
        self.__prepareMenu()
        self.__createMenu(self.menuBar(),MainWindow._actions)
        self.show()
    def __prepareMenu(self):
        m=MainWindow._actions
        m['File']['Proc']=QAction('Show proc.py',triggered=self.__showproc)
        m['File']['Proc'].setShortcut("Ctrl+P")
    def __createMenu(self,menu,actions):
        for key in actions.keys():
            if not isinstance(actions[key],dict):
                if isinstance(actions[key],QAction):
                    menu.addAction(actions[key])
                else:
                    menu.addAction(QAction(key,self,triggered=actions[key]))
            else:
                item=menu.addMenu(key)
                self.__createMenu(item,actions[key])
    def closeEvent(self,event):
        if not self.com.saveData():
            event.ignore()
            return
        ExtendMdiSubWindow.CloseAllWindows()
        event.accept()
    def __showproc(self):
        from .Widgets.PythonEditor import PythonEditor
        PythonEditor(home()+'/proc.py')
def create():
    main=MainWindow()
    return main

def addSubWindow(win):
    MainWindow._instance.area.addSubWindow(win)

def addMainMenu(namelist,function):
    act=MainWindow._actions
    for i in range(0,len(namelist)-1):
        n=namelist[i]
        if not n in act:
            act[n]={}
        act=act[n]
    act[namelist[len(namelist)-1]]=function
