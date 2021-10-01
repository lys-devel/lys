"""
Basic hook and launch QApplication. 
No pulic function and class in this file
"""

import sys
import os
import traceback
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWebEngineWidgets import QWebEngineView


def _handle_exception(exc_type, exc_value, exc_traceback):
    """ handle all exceptions """
    if issubclass(exc_type, KeyboardInterrupt):
        if QtGui.qApp:
            QtGui.qApp.quit()
        return
    filename, line, dummy, dummy = traceback.extract_tb(exc_traceback).pop()
    filename = os.path.basename(filename)

    sys.stderr.write("An error detected. This is the full error report:\n")
    sys.stderr.write("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))


def __set_qt_bindings(package):
    import builtins
    __import__ = builtins.__import__

    def hook(name, *args, **kwargs):
        root, sep, other = name.partition('.')
        if root == 'LysQt':
            name = package + sep + other
        # if root == "ExtendAnalysis":
        #    name = "lys" + sep + other
        return __import__(name, *args, **kwargs)
    builtins.__import__ = hook


sys.excepthook = _handle_exception
__set_qt_bindings("PyQt5")
app = QtWidgets.QApplication([])
