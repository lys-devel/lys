from ExtendAnalysis import *
from dask.array.core import Array as DArray
import dask.array as da


class DaskWave(WaveMethods):
    @classmethod
    def initWorkers(cls, n_workers):
        try:
            import atexit
            from dask.distributed import Client, LocalCluster
            cluster = LocalCluster(n_workers)
            cls.client = Client(cluster)
            atexit.register(lambda: cls.client.close())
            print("[DaskWave] Local cluster:", cls.client)
        except:
            print("[DaskWave] failed to init dask.distributed")

    def __init__(self, wave, axes=None, chunks="auto", note={}):
        if isinstance(wave, Wave):
            self.__fromWave(wave, axes, chunks)
        elif isinstance(wave, DArray):
            self.__fromda(wave, axes, chunks, note)
        elif isinstance(wave, DaskWave):
            self.__fromda(wave.data, wave.axes, chunks, wave.note)

    def __fromWave(self, wave, axes, chunks):
        import copy
        self.data = da.from_array(wave.data.astype(float), chunks=chunks)
        if axes is None:
            self.axes = copy.deepcopy(wave.axes)
        else:
            self.axes = copy.deepcopy(axes)
        self.note = copy.deepcopy(wave.note)

    def toWave(self):
        import copy
        w = Wave()
        res = self.data.compute()  # self.client.compute(self.data).result()
        w.data = res
        w.axes = copy.deepcopy(self.axes)
        w.note = copy.deepcopy(self.note)
        return w

    def persist(self):
        self.data = self.data.persist()  # self.client.persist(self.data)

    def __fromda(self, wave, axes, chunks, note):
        import copy
        if chunks == "NoRechunk":
            self.data = wave
        else:
            self.data = wave.rechunk(chunks)
        self.axes = copy.deepcopy(axes)
        self.note = copy.deepcopy(note)

    def sum(self, axis):
        data = self.data.sum(axis)
        axes = []
        for i, ax in enumerate(self.axes):
            if not (i in axis or i == axis):
                axes.append(ax)
        return DaskWave(data, axes=axes)

    def __getitem__(self, key):
        import copy
        if isinstance(key, tuple):
            data = self.data[key]
            axes = []
            for s, ax in zip(key, self.axes):
                if not isinstance(s, int):
                    if ax is None or (ax == np.array(None)).all():
                        axes.append(None)
                    else:
                        axes.append(ax[s])
            d = DaskWave(data, axes=axes, note=copy.deepcopy(self.note))
            d.addAnalysisLog("Wave sliced: " + str(key) + "\n")
            return d
        else:
            super().__getitem__(key)

    @staticmethod
    def SupportedFormats():
        return Wave.SupportedFormats()

    def export(self, path, type="Numpy npz (*.npz)"):
        self.toWave().export(path, type)

    def Duplicate(self):
        return DaskWave(self, chunks="NoRechunk")
