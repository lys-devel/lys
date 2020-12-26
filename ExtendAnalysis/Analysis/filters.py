from ExtendAnalysis import String
from .filter import *
import _pickle as cPickle


class Filters(object):
    def __init__(self, filters):
        self._filters = []
        self._filters.extend(filters)

    def execute(self, wave, **kwargs):
        n = 0
        while "Filter" + str(n) in wave.note:
            n += 1
        wave.addObject("Filter" + str(n), self)
        wave.addAnalysisLog("Filter Applied:" + "Filter" + str(n) + "\n")
        for f in self._filters:
            f.execute(wave, **kwargs)

    def insert(self, index, obj):
        self._filters.insert(index, obj)

    def append(self, obj):
        self._filters.append(obj)

    def getFilters(self):
        return self._filters

    def __str__(self):
        return str(cPickle.dumps(self))

    @staticmethod
    def fromString(str):
        return cPickle.loads(eval(str))

    @staticmethod
    def fromFile(path):
        s = String(path)
        return Filters.fromString(s.data)

    def saveAsFile(self, path):
        s = String((path + ".fil").replace(".fil.fil", ".fil"))
        s.data = str(self)
