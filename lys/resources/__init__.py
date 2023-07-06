import os
import numpy as np
from lys.Qt import QtGui

lysIcon = QtGui.QIcon(os.path.dirname(__file__) + "images/icon.png")
splash = {name: QtGui.QPixmap(os.path.dirname(__file__) + "/images/" + name + ".png") for name in ["clean", "dask", "local_plugin", "plugin", "start", "workspace"]}


def loadDefaultTemplate(dim):
    if dim < 6:
        with open(os.path.dirname(__file__) + "/DefaultTemplate.dic", "r") as f:
            d = eval(f.read())
        return d[str(dim) + "D"]
    return None


def gauss_3d_data():
    from lys import Wave
    x = y = np.linspace(-5, 5, 101)
    xx, yy = np.meshgrid(x, y)
    t = np.linspace(0, 100, 100, dtype=float)
    data = [np.exp(-((xx - x_0 / 20) / 0.5) ** 2 - (yy / 0.5)**2) + np.random.rand(101, 101) / 2 for x_0 in t]
    return Wave(np.array(data).transpose(1, 2, 0), x, y, t)


def load_csv():
    import numpy as np
    data = np.linspace(0, 100)
    np.savetxt("csvfile.csv", data, delimiter=",")
