
"""
Basic hook and launch QApplication. 
No pulic function and class in this file
"""

import sys
import os
import traceback

from qtpy import QtWidgets, QtGui
try:
    from qtpy import QtOpenGL
except Exception:
    pass
try:
    from qtpy import QtWebEngineWidgets
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


def start():
    sys.exit(app.exec_())


def processEvents():
    app.processEvents()
