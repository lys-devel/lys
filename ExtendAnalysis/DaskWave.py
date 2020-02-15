from ExtendAnalysis import *
from dask.array.core import Array as DArray
import dask.array as da


class DaskWave(object):
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

    def __init__(self, wave, axes=None, chunks="auto"):
        if isinstance(wave, Wave):
            self.__fromWave(wave, axes, chunks)
        elif isinstance(wave, DArray):
            self.__fromda(wave, axes, chunks)
        elif isinstance(wave, DaskWave):
            self.__fromda(wave.data, wave.axes, chunks)

    def __fromWave(self, wave, axes, chunks):
        import copy
        self.data = da.from_array(wave.data, chunks=chunks)
        if axes is None:
            self.axes = wave.axes
        else:
            self.axes = axes
        self.note = copy.copy(wave.note)

    def toWave(self):
        import copy
        w = Wave()
        res = self.data.compute()  # self.client.compute(self.data).result()
        w.data = res
        w.axes = copy.copy(self.axes)
        return w

    def persist(self):
        self.data = self.data.persist()  # self.client.persist(self.data)

    def __fromda(self, wave, axes, chunks):
        self.data = wave.rechunk(chunks)
        self.axes = axes

    def shape(self):
        return self.data.shape

    def posToPoint(self, pos, axis):
        ax = self.axes[axis]
        if (ax == np.array(None)).all():
            return int(round(pos))
        x0 = ax[0]
        x1 = ax[len(ax) - 1]
        dx = (x1 - x0) / (len(ax) - 1)
        return int(round((pos - x0) / dx))

    def sum(self, axis):
        data = self.data.sum(axis)
        axes = []
        for i, ax in enumerate(self.axes):
            if not i in axis:
                axes.append(ax)
        return DaskWave(data, axes=axes)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            data = self.data[key]
            axes = []
            for s, ax in zip(key, self.axes):
                if not isinstance(s, int):
                    if ax is None or (ax == np.array(None)).all():
                        axes.append(None)
                    else:
                        axes.append(ax[s])
            return DaskWave(data, axes=axes)
        else:
            super().__getitem__(key)
