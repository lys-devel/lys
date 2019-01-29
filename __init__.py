import  PyQt5.QtWidgets
app = PyQt5.QtWidgets.QApplication([])
from .ExtendType import *
from .LoadFile import *
from .AnalysisWindow import *
from .BasicWidgets import *
from .Tasks import *
from .Analysis import filters, filtersGUI

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
sys.excepthook = handle_exception
