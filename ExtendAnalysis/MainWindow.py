from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from .CommandWindow import CommandWindow
from .BasicWidgets import *
from .ExtendType import home
from collections import OrderedDict


class MainWindow(QMainWindow):
    _actions = OrderedDict(File={"Exit": exit})
    _instance = None

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Analysis Program Lys')
        MainWindow._instance = self
        sp = QSplitter(Qt.Horizontal)
        self.area = QMdiArea()
        ExtendMdiSubWindow.mdimain = self.area
        self.com = CommandWindow()
        sp.addWidget(self.area)
        sp.addWidget(self.com)
        self.setCentralWidget(sp)
        self.__prepareMenu()
        self.__createMenu(self.menuBar(), MainWindow._actions)
        self.show()
        AutoSavedWindow.RestoreAllWindows()

    def __prepareMenu(self):
        m = MainWindow._actions
        m['Window'] = {}
        m['Window']['Proc'] = QAction('Show proc.py', triggered=self.__showproc)
        m['Window']['Proc'].setShortcut("Ctrl+P")
        m['Window']['closeGraphs'] = QAction('Close all graphs', triggered=Graph.closeAllGraphs)
        m['Window']['closeGraphs'].setShortcut("Ctrl+K")
        m['Window']['hideSide'] = QAction('CommandWindow', triggered=self._hidecom)
        m['Window']['hideSide'].setShortcut("Ctrl+J")

    def _hidecom(self):
        if self.com.isVisible():
            self.com.hide()
        else:
            self.com.show()

    def __createMenu(self, menu, actions):
        for key in actions.keys():
            if not isinstance(actions[key], dict):
                if isinstance(actions[key], QAction):
                    menu.addAction(actions[key])
                else:
                    menu.addAction(QAction(key, self, triggered=actions[key]))
            else:
                item = menu.addMenu(key)
                self.__createMenu(item, actions[key])

    def closeEvent(self, event):
        if not self.com.saveData():
            event.ignore()
            return
        ExtendMdiSubWindow.CloseAllWindows()
        event.accept()

    def __showproc(self):
        #from .BasicWidgets.Commons.PythonEditor import PythonEditor
        PythonEditor(home() + '/proc.py')


def create():
    main = MainWindow()
    return main


def addSubWindow(win):
    MainWindow._instance.area.addSubWindow(win)


def addMainMenu(namelist, function):
    act = MainWindow._actions
    for i in range(0, len(namelist) - 1):
        n = namelist[i]
        if not n in act:
            act[n] = {}
        act = act[n]
    act[namelist[len(namelist) - 1]] = function


def addObject(*args, **kwargs):
    MainWindow._instance.com.addObject(*args, **kwargs)


def getObject(*args, **kwargs):
    return MainWindow._instance.com.getObject(*args, **kwargs)
