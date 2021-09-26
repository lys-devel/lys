from . import QtSystem
from .core import SettingDict, Wave, DaskWave
from .functions import home
from .ExtendType import *
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
