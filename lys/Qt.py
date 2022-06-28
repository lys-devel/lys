
"""
Basic hook and launch QApplication. 
No pulic function and class in this file
"""

import sys
import os
import traceback
from PyQt5 import QtWidgets, QtGui, QtCore
try:
    from PyQt5 import QtOpenGL
except Exception:
    pass
try:
    from PyQt5 import QtWebEngineWidgets
except Exception:
    pass


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


sys.excepthook = _handle_exception
app = QtWidgets.QApplication([])
