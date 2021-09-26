from scipy import interpolate
from ExtendAnalysis import *
import csv


def loadCOMSOL(file=None, size=300, method="linear"):
    if file is None:
        import pyperclip
        text = pyperclip.paste().split("\n")
        list = _readCOMSOLText(text)
    else:
        list = _readCOMSOL(file)
    print("[COMSOL] data size:", list.shape)
    if isinstance(size, tuple):
        return _parse(list, size, method)
    elif len(list[0]) == 2:
        return _parse(list, (size,), method)
    elif len(list[0]) == 3:
        return _parse(list, (size, size), method)
    elif len(list[0]) == 4:
        return _parse(list, (size, size, size), method)
    else:
        print("Multi-dimensional data requires size: e.g. size=(100,100,30) for 3d data.")


def _parse(array, size, method):
    dim = len(size)
    points = array[:, :dim]
    axes = [np.linspace(points[:, d].min(), points[:, d].max(), s)
            for d, s in enumerate(size)]
    xi = tuple(np.meshgrid(*axes))
    data = array[:, dim:]
    res = []
    for i in range(data.shape[1]):  # parallel calculation is possible
        res.append(interpolate.griddata(points, data[:, i], xi, method=method))
    data = np.array(res)
    if data.shape[0] == 1:
        data = data[0]
        w = Wave(data)
        w.axes = axes
    else:
        data = data.transpose(*list(range(len(data.shape)))[1:], 0)
        w = Wave(data)
        w.axes = axes + [None]
    return w


def _readCOMSOL(file):
    res = []
    with open(file, 'r') as f:
        reader = csv.reader(f)
        for r in reader:
            data = r[0]
            if data[0] == '%':
                continue
            for j in range(20):
                data = data.replace("  ", " ")
            data = data.split(" ")
            res.append([float(str) for str in data])
    res = np.array(res)
    return res[np.argsort(res[:, 0])]


def _readCOMSOLText(list):
    res = []
    for data in list:
        if len(data) == 0:
            continue
        if data[0] == '%':
            continue
        for j in range(20):
            data = data.replace("  ", " ")
        data = data.split(" ")
        res.append([float(str) for str in data])
    res = np.array(res)
    return res[np.argsort(res[:, 0])]
