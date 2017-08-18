import os
from ExtendAnalysis.AnalysisWindow import AnalysisWindow
from ExtendAnalysis.ExtendType import *
from .Tabs.LoadTab import *
from .Tabs.AnalysisTab import *
from .Instruments import UED_Ishizaka
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

_instruments=[UED_Ishizaka]

class UDAnalysis(AnalysisWindow):
    def __init__(self,proj):
        super().__init__("Ultrafast Diffraction/Microscopy Analysis Window",proj)
        mkdir(self.SettingFolder())
        mkdir(self.TreeFolder())
        mkdir(self.DataFolder())
        self.__tab=QTabWidget()
        self.__rawchangelistener=[]
        self.__initMenu()
        self.__tab.addTab(LoadTab(self), 'Load')
        self.__tab.addTab(AnalysisTab(self), 'Analysis')
        self.setCentralWidget(self.__tab)
        self.__loadSettings()

    def __loadSettings(self):
        self.__setting=Dict(self.SettingFolder()+"/setting.dic")
        if not "raw" in self.__setting:
            self.__setting["raw"]=None
        else:
            self.ChangeRawDataFolder(self.__setting["raw"])

    def __initMenu(self):
        menu=self.menuBar()
        data=menu.addMenu('&Data')

        raw_ac=QAction('&Raw Data Folder...',self,triggered=self.SelectRawDataFolder)
        data.addAction(raw_ac)

        ins=data.addMenu('&Instruments')
        self._grp=QActionGroup(self)
        for i in _instruments:
            act=QAction(i.name(),self,checkable=True)
            self._grp.addAction(act)
            ins.addAction(act)
            if i==_instruments[0]:
                act.setChecked(True)

    def _GetInstrument(self):
        for i in _instruments:
            if i.name()==self._grp.checkedAction().text():
                return i

    def SelectRawDataFolder(self):
        fold = QFileDialog.getExistingDirectory(self, 'Open')
        self.ChangeRawDataFolder(fold)

    def ChangeRawDataFolder(self,fold=None):
        if fold is None:
            return
        if os.path.exists(fold):
            self.__setting["raw"]=fold
            for l in self.__rawchangelistener:
                l.OnRawFolderChanged(self.__setting["raw"])
    def RawDataFolder(self):
        return self.__setting["raw"]
    def AddRawFolderChangeListener(self,listener):
        self.__rawchangelistener.append(listener)
    def DataFolder(self):
        return self.ProjectFolder()+'/Data'
    def TreeFolder(self):
        return self.SettingFolder()+'/DataTree'
    def TreeToData(self,treepath):
        target=os.path.relpath(treepath,self.TreeFolder())
        return self.DataFolder()+'/'+target
    def GetRawItems(self,path,type):
        return self._GetInstrument().GetRawItems(path,type)
    def GetRawData(self,path,type,name):
        return self._GetInstrument().GetRawData(path,type,name)
