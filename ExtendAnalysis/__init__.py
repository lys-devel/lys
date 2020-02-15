from . import QtSystem
from .ExtendType import *
from .DaskWave import *
from .LoadFile import *
from .Tasks import *
from .MainWindow import create, addMainMenu
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
