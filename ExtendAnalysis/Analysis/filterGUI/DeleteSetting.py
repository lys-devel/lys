from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from ..filtersGUI import filterGroups

class DeleteSetting(QWidget):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(None)

    @classmethod
    def _havingFilter(cls, f):
        return None

filterGroups['']=DeleteSetting
