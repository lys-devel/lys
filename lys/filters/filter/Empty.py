from lys.filters import FilterInterface


class EmptyFilter(FilterInterface):
    def __init__(self):
        pass

    def _execute(self, wave, *args, **kwargs):
        return wave

    def getParameters(self):
        return {}
