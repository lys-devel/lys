import numpy as np
import dask.array as da
from ExtendAnalysis import Wave, DaskWave
from .FilterInterface import FilterInterface


class IntegralAllFilter(FilterInterface):
    def __init__(self, axes):
        self._axes = axes

    def _execute(self, wave, **kwargs):
        data = wave.data.sum(axis=tuple(self._axes))
        ax = [wave.axes[i]
              for i in range(len(wave.axes)) if not i in self._axes]
        wave.data = data
        wave.axes = ax
        return wave

    def getAxes(self):
        return self._axes


class IntegralFilter(FilterInterface):
    def __init__(self, range):
        self._range = np.array(range)

    def _execute(self, wave, **kwargs):
        sl = []
        sumaxes = []
        for i, r in enumerate(self._range):
            if r[0] == 0 and r[1] == 0:
                sl.append(slice(None))
            else:
                ind = wave.posToPoint(r, i)
                sl.append(slice(*ind))
                sumaxes.append(i)
        key = tuple(sl)
        axes = []
        for i, (s, ax) in enumerate(zip(key, wave.axes)):
            if not i in sumaxes:
                if ax is None or (ax == np.array(None)).all():
                    axes.append(None)
                else:
                    axes.append(ax[s])
        wave.data = wave.data[key].sum(axis=tuple(sumaxes))
        wave.axes = axes
        return wave

    def getRegion(self):
        return self._range


class IntegralCircleFilter(FilterInterface):
    def __init__(self, center, radiuses, axes):
        self._center = np.array(center)
        self._radiuses = np.array(radiuses)
        self._axes = np.array(axes)

    def _execute(self, wave, **kwargs):
        region, rad = _translate_unit(
            wave, self._center, self._radiuses, self._axes)
        if isinstance(wave, Wave):
            return self._execute_wave(wave, region, rad, **kwargs)  # TODO
        if isinstance(wave, DaskWave):
            return self._execute_dask(wave, region, rad, **kwargs)
        return wave

    def _execute_dask(self, wave, region, rad, **kwargs):
        gumap = da.gufunc(_integrate_tangent, signature="(i,j),(p)->(m)",
                          output_dtypes=wave.data.dtype, vectorize=True, axes=[tuple(self._axes), (0,), (min(self._axes),)], allow_rechunk=True, output_sizes={"m": int(region[3] / region[4])})
        res = gumap(wave.data, da.from_array(region))
        wave.data = res
        wave.axes = self.__makeAxes(
            wave, *rad, self._axes)
        return wave

    def __makeAxes(self, wave, r, dr, axes):
        result = list(np.array(wave.axes))
        result.pop(max(*axes))
        result.pop(min(*axes))
        result.insert(min(*axes), np.linspace(0, r, int(r / dr)))
        return result

    def getParams(self):
        return self._center, self._radiuses, self._axes


def _translate_unit(wave, center, radiuses, axes):
    cx = wave.posToPoint(center[0], axis=axes[0])
    cy = wave.posToPoint(center[1], axis=axes[1])
    r = np.abs(wave.posToPoint(center[0] + radiuses[0], axis=axes[0]) - cx)
    dr = max(np.abs(wave.posToPoint(
        center[0] + radiuses[1], axis=axes[0]) - cx), 1)
    dr = int(dr)
    r = np.floor(r / dr) * dr
    pdr = np.abs(wave.pointToPos(
        dr, axis=axes[0]) - wave.pointToPos(0, axis=axes[0]))
    pr = np.abs(wave.pointToPos(
        r, axis=axes[0]) - wave.pointToPos(0, axis=axes[0]))
    return (cx, cy, 0, r, dr), (pr, pdr)


def _integrate_tangent(data, region):
    if len(data) <= 2:
        return np.empty((1,))
    dr = region[4]
    data = [_integrate_circle(data, (int(region[0]), int(region[1]), int(r), int(r + dr)))
            for r in range(int(region[2]), int(region[3]), int(dr))]
    return np.array(data)


def _integrate_circle(data, region):
    cx = region[0]
    cy = region[1]
    R1 = region[2]
    R2 = region[3]
    res = 0
    n = 0
    for px in _calcDonutPixels(R1, R2):
        a = abs(px[0]) - 0.5
        b = abs(px[1]) - 0.5
        if a < b:
            a, b = b, a
        y, x = cx + px[0], cy + px[1]
        if R2 <= 2:
        if x > 0 and y > 0 and x < data.shape[1] and y < data.shape[0]:
            if not np.isnan(data[y, x]):
                rat = _calcArea(a, b, R2) - _calcArea(a, b, R1)
                res += data[y, x] * rat
                n += rat
    if n == 0:
        n = 1

    return res / n


def _calcArea(a, b, r):
    if r == 0:
        return 0
    if np.sqrt((a + 1) * (a + 1) + (b + 1) * (b + 1)) <= r:
        return 1
    elif np.sqrt(a * a + b * b) <= r and np.sqrt(a * a + (b + 1) * (b + 1)) >= r:
        b1 = np.sqrt(r * r - a * a)
        return _int(r, b, b1) - a * (b1 - b)
    elif np.sqrt(a * a + (b + 1) * (b + 1)) <= r and np.sqrt((a + 1) * (a + 1) + b * b) >= r:
        return _int(r, b, b + 1) - a
    elif np.sqrt((a + 1) * (a + 1) + b * b) <= r and np.sqrt((a + 1) * (a + 1) + (b + 1) * (b + 1)) > r:
        b1 = np.sqrt(r * r - (a + 1) * (a + 1))
        return (b1 - b) + _int(r, b1, b + 1) - a * (b + 1 - b1)
    elif np.sqrt(a * a + b * b) > r:
        return 0
# calc int_a^b sqrt(r^2-x^2) dx


def _int(r, a, b):
    return 0.5 * (b * np.sqrt(r * r - b * b) + r * r * np.arcsin(b / r) - a * np.sqrt(r * r - a * a) - r * r * np.arcsin(a / r))


def _calcDonutPixels(R1, R2):
    res = []
    for y1 in range(-int(np.floor(R2 + 0.5)), int(np.floor(R2 + 0.5) + 1)):
        y1_R1 = _calcCross(y1, R1)
        y1_R2 = _calcCross(y1, R2)
        y1p_R1 = _calcCross(y1 + 0.5, R1)
        y1p_R2 = _calcCross(y1 + 0.5, R2)
        y1m_R1 = _calcCross(y1 - 0.5, R1)
        y1m_R2 = _calcCross(y1 - 0.5, R2)
        if y1m_R1 * y1p_R1 == 0:
            xmin = 0
        else:
            xmin = int(np.round(np.amin([y1_R1, y1p_R1, y1m_R1])))
        xmax = int(np.round(np.amax([y1_R2, y1p_R2, y1m_R2])))
        for x1 in range(xmin, xmax + 1):
            res.append((x1, y1))
        for x1 in range(-xmax, -xmin + 1):
            if x1 != 0:
                res.append((x1, y1))
    return res


def _calcCross(y, R):
    if abs(y) > R:
        return 0
    else:
        return np.sqrt(R * R - y * y)
