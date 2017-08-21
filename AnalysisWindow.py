from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from .ExtendType import ExtendMdiSubWindow
class AnalysisWindow(ExtendMdiSubWindow):
    def __init__(self,title,proj=None):
        super().__init__()
        self.setWindowTitle(title)
        self.__proj=proj
        #self.__initMenuBar()
        self.show()

    def __initMenuBar(self):
        menu=self.menuBar()
        fil=menu.addMenu('&File')
        ex=QAction('Exit',self,triggered=self.close)
        fil.addAction(ex)

        grf=menu.addMenu('&Graph')
        self.__prev=QAction('Auto Preview',self,checkable=True)
        grf.addAction(self.__prev)
    def showPreview(self,wave):
        if self.__prev.isChecked():
            PreviewWindow(wave)
    def ProjectFolder(self):
        return self.__proj
    def SettingFolder(self):
        return self.ProjectFolder()+'/_settings'
