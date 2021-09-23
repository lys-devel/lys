from . import QtSystem
from .core import SettingDict
from .ExtendType import *
from .DaskWave import *
from .LoadFile import *
from .Tasks import *
from .MainWindow import create, addMainMenu, addObject, getObject
from .BasicWidgets import *
from .AnalysisWindow import *
from .Analysis import filters, filtersGUI, MultiCut


def createMainWindow():
    create()
    QtSystem.systemExit()


def makeMainWindow():
    create()


def exitMainWindow():
    QtSystem.systemExit()
