from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import  PyQt5.QtWidgets
from PyQt5 import QtGui
__app = PyQt5.QtWidgets.QApplication([])

from .ExtendType import *
from .LoadFile import *
from .AnalysisWindow import *
from .BasicWidgets import *
from .Tasks import *
from .MainWindow import create, addMainMenu
from .Analysis import filters, filtersGUI, MultiCut

def handle_exception(exc_type, exc_value, exc_traceback):
    """ handle all exceptions """
    if issubclass(exc_type, KeyboardInterrupt):
        if QtGui.qApp:
            QtGui.qApp.quit()
        return
    import traceback
    filename, line, dummy, dummy = traceback.extract_tb( exc_traceback ).pop()
    filename = os.path.basename( filename )
    error    = "%s: %s" % ( exc_type.__name__, exc_value )

    sys.stderr.write("An error detected. This is the full error report:\n")
    sys.stderr.write("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    #sys.exit(1)

def createMainWindow():
    create()
    sys.exit(__app.exec())

def makeMainWindow():
    create()

def exitMainWindow():
    sys.exit(__app.exec())

sys.excepthook = handle_exception
