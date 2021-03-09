import cv2
import numpy as np

from ExtendAnalysis import Wave, DaskWave
from .FilterInterface import FilterInterface


class AdaptiveThresholdFilter(FilterInterface):
    def __init__(self, size, c, mode='Median'):
        self._size = size
        self._c = c
        self._method = mode

    def _execute(self, wave, **kwargs):
        args = self._loadArgs()
        wave.data = cv2.adaptiveThreshold(np.array(wave.data / np.max(wave.data) * 255, dtype=np.uint8), *args)
        return wave

    def _loadArgs(self):
        bs = self._size
        c = self._c
        if self._method == 'Median':
            mode = cv2.ADAPTIVE_THRESH_MEAN_C
        else:
            mode = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
        return [1, mode, cv2.THRESH_BINARY_INV, bs, c]

    def getParams(self):
        return self._size, self._c, self._method


class ThresholdFilter(FilterInterface):
    def __init__(self, threshold):
        self._threshold = threshold

    def _execute(self, wave, **kwargs):
        if isinstance(wave, Wave):
            wave.data = np.where(wave.data > self._threshold, 1, 0)
        if isinstance(wave, DaskWave):
            wave.data = wave.data.copy()
            wave.data[wave.data < self._threshold] = 0
            wave.data[wave.data >= self._threshold] = 1
        return wave

    def getParams(self):
        return self._threshold
