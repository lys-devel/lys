from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from .ExtendType import *
class AnalysisWindow(ExtendMdiSubWindow):
    def __init__(self,title,proj=None):
        set=globalSetting()
        if "Floating" in set:
            b=set["Floating"]
        else:
            b=False
        super().__init__(title,floating=b)
        self.__proj=proj
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
