"""Basic hook and launch QApplication"""
import sys
import os
from PyQt5 import QtWidgets, QtGui


def __handle_exception(exc_type, exc_value, exc_traceback):
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


def __set_qt_bindings(package):
    import builtins
    __import__ = builtins.__import__

    def hook(name, *args, **kwargs):
        root, sep, other = name.partition('.')
        if root == 'LysQt':
            name = package + sep + other
        return __import__(name, *args, **kwargs)
    builtins.__import__ = hook


sys.excepthook = __handle_exception
__set_qt_bindings("PyQt5")
app = QtWidgets.QApplication([])
