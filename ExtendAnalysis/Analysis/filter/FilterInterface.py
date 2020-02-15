from ExtendAnalysis import Wave, DaskWave


class FilterInterface(object):
    def execute(self, wave, **kwargs):
        if isinstance(wave, Wave) or isinstance(wave, DaskWave) or isinstance(wave, np.array):
            self._execute(wave, **kwargs)
        if hasattr(wave, "__iter__"):
            for w in wave:
                self.execute(w, **kwargs)

    def _execute(self, wave, **kwargs):
        pass
