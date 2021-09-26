from LysQt.QtWidgets import QMainWindow, QMdiArea, QSplitter
from LysQt.QtCore import Qt
from .CommandWindow import CommandWindow
from .BasicWidgets import *
from . import home


class MainWindow(QMainWindow):
    _instance = None

    def __init__(self):
        super().__init__()
        MainWindow._instance = self
        self.__initUI()
        self.__initMenu()
        ExtendMdiSubWindow.mdimain = self.area
        AutoSavedWindow.RestoreAllWindows()

    def __initUI(self):
        self.setWindowTitle('lys')
        self.area = QMdiArea()
        self.com = CommandWindow()

        sp = QSplitter(Qt.Horizontal)
        sp.addWidget(self.area)
        sp.addWidget(self.com)
        self.setCentralWidget(sp)
        self.show()

    def __initMenu(self):
        menu = self.menuBar()
        file = menu.addMenu("File")

        act = file.addAction("Exit")
        act.triggered.connect(exit)

        win = menu.addMenu("Window")

        act = win.addAction("Show proc.py")
        act.triggered.connect(self.__showproc)
        act.setShortcut("Ctrl+P")

        act = win.addAction("Close all graphs")
        act.triggered.connect(Graph.closeAllGraphs)
        act.setShortcut("Ctrl+K")

        act = win.addAction("Show/Hide Command Window")
        act.triggered.connect(lambda: self.com.setVisible(not self.com.isVisible()))
        act.setShortcut("Ctrl+J")
        return

    def closeEvent(self, event):
        if not self.com.saveData():
            event.ignore()
            return
        ExtendMdiSubWindow.CloseAllWindows()
        event.accept()

    def __showproc(self):
        #from .BasicWidgets.Commons.PythonEditor import PythonEditor
        PythonEditor(home() + '/proc.py')


def addSubWindow(win):
    MainWindow._instance.area.addSubWindow(win)


def _getMainMenu():
    return MainWindow._instance.menuBar()


def addObject(*args, **kwargs):
    MainWindow._instance.com.addObject(*args, **kwargs)


def getObject(*args, **kwargs):
    return MainWindow._instance.com.getObject(*args, **kwargs)
