import sys
from .filter import *
import _pickle as cPickle
import lys


class Filters(object):
    def __init__(self, filters):
        self._filters = []
        self._filters.extend(filters)

    def execute(self, wave, **kwargs):
        n = 0
        # while "Filter" + str(n) in wave.note:
        #    n += 1
        #wave.note.addObject("Filter" + str(n), self)
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
    def fromString(data):
        if isinstance(data, str):
            data = eval(data)
        data = data.replace(b"ExtendAnalysis", b"lys")
        res = cPickle.loads(data)
        return res

    @staticmethod
    def fromFile(path):
        with open(path, 'r') as f:
            data = f.read()
        return Filters.fromString(data)

    def saveAsFile(self, path):
        with open((path + ".fil").replace(".fil.fil", ".fil"), 'w') as f:
            f.write(str(self))
