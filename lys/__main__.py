"""
lys main module.
To see help of lys, type [python -m lys -h]
"""

import shutil
import argparse
import datetime
from importlib import import_module

# QApplication is created in main Package
import lys
from lys.Qt import QtWidgets, QtCore
from lys.resources import splash


class Load_Window(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet("QWidget{background-color: #191970}")
        self.__initlayout()

    def __initlayout(self):
        self._label = QtWidgets.QLabel()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)
        self.setLayout(layout)

    def setPixmap(self, p):
        self._label.setPixmap(p)
        self.show()
        lys.Qt.processEvents()


loadWindow = Load_Window()
loadWindow.setPixmap(splash["start"])

# Help
parser = argparse.ArgumentParser(prog='lys', usage="python -m lys (options)", add_help=True)
# Launch local cluster
parser.add_argument("-n", "--ncore", help="Launch local cluster with NCORE", type=int, required=False)
# Plugins
parser.add_argument("-p", "--plugin", help="Import plugins", nargs="*", required=False)
# NoPlugins
parser.add_argument("-np", "--noplugin", help="Do not import local plugins", action="store_true")
# Clean
parser.add_argument("--clean", help="Delete all settings. Try it when lys is broken", action="store_true")

# parse args
args = parser.parse_args()

if args.clean:
    loadWindow.setPixmap(splash["clean"])
    shutil.rmtree(".lys")

# Launch local cluster
if args.ncore is not None:
    loadWindow.setPixmap(splash["dask"])
    lys.DaskWave.initWorkers(args.ncore)

# Create main window
lys.glb.createMainWindow(show=False)

# Load local Plugins
if not args.noplugin:
    loadWindow.setPixmap(splash["local_plugin"])
    from . import localPlugins

    # Load Plugins
    loadWindow.setPixmap(splash["plugin"])
    if args.plugin is not None:
        for plugin in args.plugin:
            import_module(plugin)
else:
    print("lys is launched wih -np option. No plugin is loaded.")

loadWindow.setPixmap(splash["workspace"])
lys.glb.restoreWorkspaces()
loadWindow.setPixmap(splash["start"])
lys.glb.mainWindow().show()
loadWindow.close()
print("\n------------ Session start at " + str(datetime.datetime.now()) + " -------------")
lys.Qt.start()
