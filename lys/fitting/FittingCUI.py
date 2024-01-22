import uuid
import inspect
import itertools
import numpy as np

from lys import Wave
from lys.Qt import QtCore

from .Functions import functions
from .Fitting import fit, sumFunction


class FittingCUI(QtCore.QObject):
    def __init__(self, wave):
        super().__init__()
        self._data = wave
        self._funcs = _FittingFunctions()
        if "lys_Fitting" in wave.note:
            self.loadFromDictionary(wave.note["lys_Fitting"])
        else:
            self._range = [None, None]
            self._xdata = None
            self._id = uuid.uuid1()
        self._funcs.updated.connect(self.__update)

    def __getattr__(self, key):
        if "_funcs" in self.__dict__:
            if hasattr(self._funcs, key):
                return getattr(self._funcs, key)
        return super().__getattr__(key)

    def __update(self):
        self._data.note["lys_Fitting"] = self.saveAsDictionary()

    def dataForFit(self):
        wave = self._data
        axis = wave.x
        range = list(self._range)
        if range[0] is None:
            range[0] = np.min(axis) - 1
        if range[1] is None:
            range[1] = np.max(axis) + 1
        p = wave.posToPoint(range, axis=0)
        if self._xdata is None:
            x = wave.x
        else:
            x = wave.note[self._xdata]
        return wave.data[p[0]:p[1] + 1], x[p[0]:p[1] + 1], wave.x[p[0]:p[1] + 1]

    def fit(self):
        guess = self.fitParameters
        bounds = self.fitBounds
        for g, b in zip(guess, bounds):
            if g < b[0] or g > b[1] or b[0] > b[1]:
                return False, "Fit error: all fitting parameters should between minimum and maximum."
        data, x, _ = self.dataForFit()
        res, sig = fit(self.fitFunction, x, data, guess=guess, bounds=bounds.T)
        n = 0
        for fi in self.functions:
            m = len(fi.parameters)
            fi.setValue(res[n:n + m])
            n = n + m
        return True, "OK"

    def fittedData(self):
        wave = self._data
        f = self.fitFunction
        p = self.fitParameters
        data, x, axis = self.dataForFit()
        return Wave(f(x, *p), axis, name=wave.name + "_fit", lys_Fitting={"fitted": False, "id": self._id})

    def residualSum(self):
        data, _, _ = self.dataForFit()
        fitted = self.fittedData()
        return np.sqrt(np.sum(abs(data - fitted.data)**2) / len(data))

    def setFittingRange(self, type, range):
        self._range = range
        self._xdata = type
        self.__update()

    def getFittingRange(self):
        return self._xdata, self._range

    def saveAsDictionary(self, useId=True):
        d = self._funcs.saveAsDictionary()
        d["fitted"] = True
        d["range"] = self._range
        d["xdata"] = self._xdata
        if useId:
            d["id"] = self._id
        return d

    def loadFromDictionary(self, dic):
        self._funcs.loadFromDictionary(dic)
        self._range = dic.get("range", [None, None])
        self._xdata = dic.get("xdata", None)
        if "id" in dic:
            self._id = dic["id"]

    @property
    def name(self):
        return self._data.name

    @property
    def id(self):
        return self._id


class _FittingFunctions(QtCore.QObject):
    functionAdded = QtCore.pyqtSignal(object)
    functionRemoved = QtCore.pyqtSignal(object)
    updated = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self._funcs = []

    @property
    def functions(self):
        return self._funcs

    def addFunction(self, func):
        if isinstance(func, dict):
            item = _FuncInfo.loadFromDictionary(func)
        else:
            item = _FuncInfo(func)
        item.updated.connect(self.updated)
        self._funcs.append(item)
        self.functionAdded.emit(item)
        self.updated.emit()

    def removeFunction(self, index):
        del self._funcs[index]
        self.functionRemoved.emit(index)
        self.updated.emit()

    def clear(self):
        while len(self.functions) != 0:
            self.removeFunction(0)

    def getParamValue(self, index_f, index_p):
        if len(self.functions) > index_f:
            f = self.functions[index_f]
            if len(f.value) > index_p:
                return f.value[index_p]

    def saveAsDictionary(self):
        return {"function_" + str(i): f.saveAsDictionary() for i, f in enumerate(self.functions)}

    def loadFromDictionary(self, dic):
        self.clear()
        i = 0
        while "function_" + str(i) in dic:
            self.addFunction(dic["function_" + str(i)])
            i += 1

    @property
    def fitFunction(self):
        if len(self._funcs) == 0:
            return None
        return sumFunction([fi.function for fi in self._funcs])

    @property
    def fitParameters(self):
        return np.array(list(itertools.chain(*[fi.value for fi in self._funcs])))

    @property
    def fitBounds(self):
        return np.array(list(itertools.chain(*[fi.range for fi in self._funcs])))



class _FuncInfo(QtCore.QObject):
    updated = QtCore.pyqtSignal()

    def __init__(self, name):
        super().__init__()
        self._name = name
        param = inspect.signature(functions[name]).parameters
        self._params = [_ParamInfo(n, p) for n, p in zip(list(param.keys())[1:], list(param.values())[1:])]
        for p in self._params:
            p.stateChanged.connect(self.updated)

    def setValue(self, value):
        for p, v in zip(self.parameters, value):
            p.setValue(v)

    @property
    def name(self):
        return self._name

    @property
    def parameters(self):
        return self._params

    @property
    def function(self):
        return functions[self._name]

    @property
    def paramNames(self):
        return [p.name for p in self.parameters]

    @property
    def value(self):
        return [p.value for p in self.parameters]

    @property
    def range(self):
        res = []
        for p in self.parameters:
            if p.enabled:
                b = list(p.range)
                min_enabled, max_enabled = p.minMaxEnabled
                if not min_enabled:
                    b[0] = -np.inf
                if not max_enabled:
                    b[1] = np.inf
                res.append(tuple(b))
            else:
                res.append((p.value, p.value))
        return res

    def saveAsDictionary(self):
        d = {"param_" + str(i): p.saveAsDictionary() for i, p in enumerate(self.parameters)}
        d["name"] = self._name
        return d

    @classmethod
    def loadFromDictionary(cls, dic):
        obj = cls(dic["name"])
        for i, p in enumerate(obj.parameters):
            p.loadParameters(**dic["param_" + str(i)])
        return obj


class _ParamInfo(QtCore.QObject):
    stateChanged = QtCore.pyqtSignal(object)

    def __init__(self, name, param, value=None, range=(0, 1), enabled=True, minMaxEnabled=(False, False)):
        super().__init__()
        self._name = name
        if param.default != inspect._empty:
            self._value = param.default
        else:
            self._value = 1
        if value is not None:
            self._value = value
        self._range = range
        self._use = enabled
        self._min, self._max = minMaxEnabled

    @property
    def name(self):
        return self._name

    def setValue(self, value):
        self._value = value
        self.stateChanged.emit(self)

    @property
    def value(self):
        return self._value

    def setEnabled(self, b):
        self._use = b
        self.stateChanged.emit(self)

    @property
    def enabled(self):
        return self._use

    def setRange(self, min=None, max=None):
        if min is not None:
            self._range[0] = min
        if max is not None:
            self._range[1] = max
        self.stateChanged.emit(self)

    @property
    def range(self):
        return tuple(self._range)

    def setMinMaxEnabled(self, min, max):
        self._min = min
        self._max = max

    @property
    def minMaxEnabled(self):
        return self._min, self._max

    def saveAsDictionary(self):
        return {"name": self._name, "value": self.value, "range": self.range, "enabled": self.enabled, "minMaxEnabled": self.minMaxEnabled}

    def loadParameters(self, name, value, range, enabled, minMaxEnabled):
        self._name = name
        self._value = value
        self._range = range
        self._use = enabled
        self._min, self._max = minMaxEnabled
