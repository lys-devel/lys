from PyQt5.QtWidgets import *
from .ExtendShell import ExtendShell
from .GraphWindow import AutoSavedWindow, PreviewWindow, ExtendMdiSubWindow

class MainWindow(QMainWindow):
    _actions={"File":{"Exit":exit}}
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
        self.__createMenu(self.menuBar(),MainWindow._actions)
        self.show()
    def __createMenu(self,menu,actions):
        for key in actions.keys():
            if not isinstance(actions[key],dict):
                menu.addAction(QAction(key,self,triggered=actions[key]))
            else:
                item=menu.addMenu(key)
                self.__createMenu(item,actions[key])
    def closeEvent(self,event):
        self.com.saveData()
        ExtendMdiSubWindow.CloseAllWindows()
        event.accept()

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
