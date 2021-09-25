from . import QtSystem as Qt
from .core import SettingDict, Wave
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
    Qt.systemExit()


def makeMainWindow():
    create()


def exitMainWindow():
    Qt.systemExit()
