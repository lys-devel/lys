from PyQt5.QtWidgets import *
from ExtendAnalysis import *

class MainWindow(QMainWindow):
    _actions={"File":{"Exit":exit}}
    _instance=None
    def __init__(self):
        from ExtendAnalysis.ExtendShell import ExtendShell
        from GraphWindow import AutoSavedWindow
        super().__init__()
        MainWindow._instance=self
        self.area=QMdiArea()
        self.setCentralWidget(self.area)
        AutoSavedWindow.mdimain=self.area
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
        from ExtendShell import ExtendShell
        from GraphWindow import AutoSavedWindow, PreviewWindow
        from AnalysisWindow import AnalysisWindow
        self.com.saveData()
        AutoSavedWindow.CloseAllWindows()
        AnalysisWindow.CloseAllWindows()
        PreviewWindow.CloseAllWindows()
        event.accept()

def create():
    main=MainWindow()
    return main

def addSubWindow(win):
    MainWindow._instance.area.addSubWindow(win)

def addAction(namelist,function):
    act=MainWindow._actions
    for i in range(0,len(namelist)-1):
        n=namelist[i]
        if not n in act:
            act[n]={}
        act=act[n]
    act[namelist[len(namelist)-1]]=function
