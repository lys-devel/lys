
from lys import DaskWave
from .FilterInterface import FilterInterface


class RechunkFilter(FilterInterface):
    """
    Rechunk dask array

    Users should proper chunk size for efficient parallel calculation for dask array.

    RechunkFilter enables users to rechunk dask array manually.

    See dask manual (https://docs.dask.org/en/latest/array-chunks.html) for detail.

    Args:
        chunks('auto' or tuple of int): chunk size.
    """

    def __init__(self, chunks="auto"):
        self._chunks = chunks

    def _execute(self, wave, *args, **kwargs):
        return DaskWave(wave, chunks=self._chunks)

    def getParameters(self):
        return {"chunks": self._chunks}
