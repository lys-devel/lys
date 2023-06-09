"""
This is a template to create new window in lys. This file works without edit.
You can create window by calling WindowName() in the command line.
"""

from lys.widgets import LysSubWindow
from lys.Qt import QtWidgets, QtGui, QtCore  # We recommend to load Qt like this.


class WindowName(LysSubWindow):  # LysSubWindow inherits QMdiSubWindow.
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WindowName")
        self._initUI()

    def _initUI(self):
        # Initialize the widget here. This is an example.
        self._val1 = QtWidgets.QSpinBox()
        self._btn1 = QtWidgets.QPushButton("OK", clicked=lambda: print("value:", self._val1.value()))
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self._val1)
        layout.addWidget(self._btn1)

        w = QtWidgets.QWidget()
        w.setLayout(layout)
        self.setWidget(w)  # QMdiSubWindow only accepts widget, not layout.
