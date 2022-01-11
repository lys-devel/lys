import warnings
import numpy as np
from matplotlib.colors import hsv_to_rgb
from lys.errors import NotImplementedWarning

from .CanvasBase import saveCanvas
from .WaveData import WaveData


class RGBData(WaveData):
    """
    Interface to access rgb data in the canvas.

    Instance of RGBData is automatically generated by display or append methods.
    """

    def __setAppearance(self, key, value):
        self._appearance[key] = value

    def __getAppearance(self, key, default=None):
        return self._appearance.get(key, default)

    @saveCanvas
    def setColorRange(self, min='auto', max='auto'):
        """
        Set the color range of the image.

        Args:
            min(float or 'auto'): The minimum value of the range.
            max(float or 'auto'): The maximum value of the range.
        """
        self.__setAppearance('Range', (min, max))
        self._update()

    def getColorRange(self):
        """
        Get the color range of the image.

        Return:
            tuple of length 2: minimum and maximum value of the range.
        """
        return self.__getAppearance('Range')

    def getAutoColorRange(self):
        """
        Get the automarically-calculated color range of the image, which is used by :meth:`setColorRange` method.

        Return:
            tuple of length 2: minimum and maximum value of the range.
        """
        return (0, np.max(np.abs(self.getWave().data)))

    @saveCanvas
    def setColorRotation(self, rot):
        """
        Rotate color map of the RGB image.

        Args:
            rot(float): The rotation.
        """
        self.__setAppearance('ColorRotation', rot)
        self._update()

    def getColorRotation(self):
        """
        Get color rotation of the RGB image.

        Return:
            float: The rotation.
        """
        return self.__getAppearance('ColorRotation')

    def getRGBWave(self):
        return self._makeRGBData(self.getFilteredWave(), self.saveAppearance())

    def _makeRGBData(self, wav, appearance):
        wav = wav.duplicate()
        if wav.data.ndim == 2:
            if 'Range' in appearance:
                rmin, rmax = appearance['Range']
            else:
                rmin, rmax = 0, np.max(np.abs(wav.data))
            wav.data = self._Complex2HSV(wav.data, rmin, rmax, appearance.get('ColorRotation', 0))
        elif wav.data.ndim == 3:
            if 'Range' in appearance:
                rmin, rmax = appearance['Range']
                amp = np.where(wav.data < rmin, rmin, wav.data)
                amp = np.where(amp > rmax, rmax, amp)
                wav.data = (amp - rmin) / (rmax - rmin)
        return wav

    def _Complex2HSV(self, z, rmin, rmax, hue_start=0):
        amp = np.abs(z)
        amp = np.where(amp < rmin, rmin, amp)
        amp = np.where(amp > rmax, rmax, amp)
        ph = np.angle(z, deg=1) + hue_start
        h = (ph % 360) / 360
        s = np.ones_like(h)
        v = (amp - rmin) / (rmax - rmin)
        rgb = hsv_to_rgb(np.dstack((h, s, v)))
        return rgb

    def _loadAppearance(self, appearance):
        self.setColorRange(*appearance.get('Range', self.getAutoColorRange()))
        self.setColorRotation(appearance.get('ColorRotation', 0))