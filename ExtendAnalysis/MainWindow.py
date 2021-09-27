import os

from LysQt.QtWidgets import QMainWindow, QMdiArea, QSplitter
from LysQt.QtCore import Qt, pyqtSignal
from .BasicWidgets import *
from . import home, plugin

from .CommandWindow import *


class MainWindow(QMainWindow):
    closed = pyqtSignal(object)
    _instance = None

    def __init__(self):
        super().__init__()
        MainWindow._instance = self
        self.__loadData()
        self.__initUI()
        self.__initMenu()
        ExtendMdiSubWindow.mdimain = self.area
        AutoSavedWindow.RestoreAllWindows()

    def __loadData(self):
        if not os.path.exists('proc.py'):
            with open("proc.py", "w") as file:
                file.write("from ExtendAnalysis import *")

    def __initUI(self):
        self.setWindowTitle('lys')
        self.area = QMdiArea()
        self._side = self.__sideBar()

        sp = QSplitter(Qt.Horizontal)
        sp.addWidget(self.area)
        sp.addWidget(self._side)
        self.setCentralWidget(sp)
        self.show()

    def __sideBar(self):
        self.output = CommandLogWidget(self)

        self._tab_up = QTabWidget()
        self._tab_up.addTab(self.output, "Command")

        self._tab = QTabWidget()
        self._tab.addTab(FileWidget(self, plugin.shell()), "File")
        self._tab.addTab(WorkspaceWidget(self), "Workspace")
        self._tab.addTab(TaskWidget(), "Tasks")
        self._tab.addTab(SettingWidget(), "Settings")

        layout_h = QSplitter(Qt.Vertical)
        layout_h.addWidget(self._tab_up)
        layout_h.addWidget(CommandLineEdit(plugin.shell()))
        layout_h.addWidget(self._tab)

        lay = QHBoxLayout()
        lay.addWidget(layout_h)
        w = QWidget()
        w.setLayout(lay)
        return w

    def __initMenu(self):
        menu = self.menuBar()
        file = menu.addMenu("File")

        act = file.addAction("Exit")
        act.triggered.connect(exit)

        win = menu.addMenu("Window")

        act = win.addAction("Close all graphs")
        act.triggered.connect(Graph.closeAllGraphs)
        act.setShortcut("Ctrl+K")

        act = win.addAction("Show/Hide Sidebar")
        act.triggered.connect(lambda: self._side.setVisible(not self._side.isVisible()))
        act.setShortcut("Ctrl+J")
        return

    def closeEvent(self, event):
        if not self.__saveData():
            event.ignore()
            return
        self.closed.emit(event)
        if not event.isAccepted():
            return
        ExtendMdiSubWindow.CloseAllWindows()

    def __saveData(self):
        AutoSavedWindow.StoreAllWindows()
        return True

    def addTab(self, widget, name, position):
        if position == "up":
            self._tab_up.addTab(widget, name)
        if position == "down":
            self._tab.addTab(widget, name)


def addSubWindow(win):
    MainWindow._instance.area.addSubWindow(win)
