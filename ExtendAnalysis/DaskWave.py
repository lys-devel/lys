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
        if hasattr(pos, "__iter__"):
            return [self.posToPoint(p, axis) for p in pos]
        ax = self.axes[axis]
        if (ax == np.array(None)).all():
            return int(round(pos))
        x0 = ax[0]
        x1 = ax[len(ax) - 1]
        dx = (x1 - x0) / (len(ax) - 1)
        return int(round((pos - x0) / dx))

    def pointToPos(self, p, axis=None):
        if axis is None:
            x0 = self.x[0]
            x1 = self.x[len(self.x) - 1]
            y0 = self.y[0]
            y1 = self.y[len(self.y) - 1]
            dx = (x1 - x0) / (len(self.x) - 1)
            dy = (y1 - y0) / (len(self.y) - 1)
            return (p[0] * dx + x0, p[1] * dy + y0)
        else:
            if hasattr(p, "__iter__"):
                return [self.pointToPos(pp, axis) for pp in p]
            ax = self.getAxis(axis)
            x0 = ax[0]
            x1 = ax[len(ax) - 1]
            dx = (x1 - x0) / (len(ax) - 1)
            # return int(round((pos - x0) / dx))
            return p*dx+x0

    def getAxis(self, dim):
        val = np.array(self.axes[dim])
        if self.data.ndim <= dim:
            return None
        elif val.ndim == 0:
            return np.arange(self.data.shape[dim])
        else:
            if self.data.shape[dim] == val.shape[0]:
                return val
            else:
                res = np.empty((self.data.shape[dim]))
                for i in range(self.data.shape[dim]):
                    res[i] = np.NaN
                for i in range(min(self.data.shape[dim], val.shape[0])):
                    res[i] = val[i]
                return res

    def sum(self, axis):
        data = self.data.sum(axis)
        axes = []
        for i, ax in enumerate(self.axes):
            if not (i in axis or i == axis):
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

    def axisIsValid(self, dim):
        tmp = self.axes[dim]
        if tmp is None or (tmp == np.array(None)).all():
            return False
        return True

    @staticmethod
    def SupportedFormats():
        return Wave.SupportedFormats()

    def export(self, path, type="Numpy npz (*.npz)"):
        self.toWave().export(path, type)
