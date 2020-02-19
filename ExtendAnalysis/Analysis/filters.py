from .filter import *
import _pickle as cPickle

class Filters(object):
    def __init__(self, filters):
        self._filters = []
        self._filters.extend(filters)

    def execute(self, wave, **kwargs):
        for f in self._filters:
            f.execute(wave, **kwargs)

    def insert(self, index, obj):
        self._filters.insert(index, obj)

    def getFilters(self):
        return self._filters

    def __str__(self):
        return str(cPickle.dumps(self))

    @staticmethod
    def fromString(str):
        return cPickle.loads(eval(str))
