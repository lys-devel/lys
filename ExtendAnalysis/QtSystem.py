import sys
import os
import PyQt5
import PyQt5.QtWidgets
from PyQt5 import QtGui

__app = PyQt5.QtWidgets.QApplication([])


def systemExit():
    sys.exit(__app.exec())


def handle_exception(exc_type, exc_value, exc_traceback):
    """ handle all exceptions """
    if issubclass(exc_type, KeyboardInterrupt):
        if QtGui.qApp:
            QtGui.qApp.quit()
        return
    import traceback
    filename, line, dummy, dummy = traceback.extract_tb(exc_traceback).pop()
    filename = os.path.basename(filename)

    sys.stderr.write("An error detected. This is the full error report:\n")
    sys.stderr.write("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))


sys.excepthook = handle_exception
