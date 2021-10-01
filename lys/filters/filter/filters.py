import sys
import _pickle as cPickle
from .FilterInterface import FilterInterface


class Filters(FilterInterface):
    def __init__(self, filters):
        self._filters = []
        if isinstance(filters, Filters):
            self._filters.extend(filters._filters)
        else:
            self._filters.extend(filters)

    def _execute(self, wave, **kwargs):
        for f in self._filters:
            wave = f.execute(wave, **kwargs)
        return wave

    def getParameters(self):
        return {"filters": self._filters}

    def getRelativeDimension(self):
        return sum([f.getRelativeDimension() for f in self._filters])

    def __str__(self):
        result = []
        for f in self._filters:
            d = f.getParameters()
            d["filterName"] = f.__class__.__name__
            result.append(d)
        return str(result)

    def insert(self, index, obj):
        self._filters.insert(index, obj)

    def append(self, obj):
        self._filters.append(obj)

    def getFilters(self):
        return self._filters

    @staticmethod
    def fromString(data):
        if isinstance(data, str):
            data = eval(data)
        if isinstance(data, list):
            res = Filters._restoreFilter(data)
        else:  # backward compability
            data = data.replace(b"ExtendAnalysis.Analysis.filters", b"lys.filters")
            data = data.replace(b"ExtendAnalysis.Analysis.filter", b"lys.filters.filter")
            res = cPickle.loads(data)
        return res

    @staticmethod
    def _restoreFilter(data):
        from lys import filters
        # parse from list of parameter dictionary
        result = []
        for f in data:
            fname = f["filterName"]
            del f["filterName"]
            if fname in filters._filterClasses:
                result.append(filters._filterClasses[fname](**f))
            else:
                print("Could not load " + fname + ". The filter class may be deleted or not loaded. Check plugins and their version.", file=sys.stderr)
                return None
        return Filters(result)

    @staticmethod
    def fromFile(path):
        with open(path, 'r') as f:
            data = f.read()
        return Filters.fromString(data)

    def saveAsFile(self, path):
        if not path.endswith(".fil"):
            path = path + ".fil"
        with open(path, 'w') as f:
            f.write(str(self))
