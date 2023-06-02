import os
from lys.Qt import QtGui

lysIcon = QtGui.QIcon(os.path.dirname(__file__) + "/icon.png")
splash = {name: QtGui.QPixmap(os.path.dirname(__file__) + "/splash/" + name + ".png") for name in ["clean", "dask", "local_plugin", "plugin", "start", "workspace"]}
