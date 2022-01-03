
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .SaveCanvas import *


class AnnotGUICanvasBase(object):
    def __init__(self):
        self.__mode = "range"

    def constructContextMenu(self, menu):
        m = menu.addMenu('Tools')
        m.addAction(QAction('Select Range', self, triggered=self.__range))
        m.addAction(QAction('Draw Line', self, triggered=self.__line))
        m.addAction(QAction('Draw Rectangle', self, triggered=self.__rect))
        return menu

    def __line(self):
        self.__mode = "line"

    def __range(self):
        self.__mode = "range"

    def __rect(self):
        self.__mode = "rect"

    def _getMode(self):
        return self.__mode
