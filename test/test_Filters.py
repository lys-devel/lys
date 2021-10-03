import unittest
import os
import warnings
import shutil

import numpy as np
from scipy import signal

from numpy.testing import assert_array_equal, assert_array_almost_equal

from lys import Wave, DaskWave, filters


class Filters_test(unittest.TestCase):
    path = "test/Filters"

    def setUp(self):
        # suppress deprecated warnings in dask_image because
        # Although it is fixed in latest version on GitHub, PyPi version is deprecated.
        warnings.simplefilter('ignore')
        os.makedirs(self.path, exist_ok=True)

    def tearDown(self):
        warnings.resetwarnings()
        shutil.rmtree(self.path)

    def test_FilterInterface(self):
        w = Wave(np.ones([3, 4]), [1, 2, 3], [1, 2, 3, 4])
        f = filters.IntegralAllFilter(axes=[0], sumtype="Sum")

        # execute(Wave)
        result1 = f.execute(w)
        self.assertTrue((result1.data == [3, 3, 3, 3]).all())

        # execute(np.array)
        result2 = f.execute(w.data)
        self.assertTrue((result2 == [3, 3, 3, 3]).all())

        # execute(DaskWave)
        result3 = f.execute(DaskWave(w)).compute()
        self.assertTrue((result3.data == [3, 3, 3, 3]).all())

        # save & load
        f.saveAsFile(self.path + "/test1.fil")
        loaded = filters.fromFile(self.path + "/test1.fil")
        self.assertEqual(str(loaded), str(filters.Filters([f])))

    def test_Filters(self):
        w = Wave(np.ones([3, 4, 5]), [1, 2, 3], [1, 2, 3, 4], [1, 2, 3, 4, 5])
        f = filters.IntegralAllFilter(axes=[0], sumtype="Sum")
        fs = filters.Filters([f, f])

        # dimension check
        self.assertEqual(fs.getRelativeDimension(), -2)

        # simple execute
        result1 = fs.execute(w)
        self.assertTrue((result1.data == [12, 12, 12, 12, 12]).all())

        # save & load
        fs.saveAsFile(self.path + "/test2.fil")
        loaded = filters.fromFile(self.path + "/test2.fil")
        self.assertEqual(str(loaded), str(fs))

    def test_convolution(self):
        # PrewittFilter
        w = Wave([1, 2, 3, 4, 5], [1, 2, 3, 4, 5], name="wave")
        f = filters.PrewittFilter(axes=[0])
        f1 = filters.PrewittFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [1, 2, 2, 2, 1])
        assert_array_equal(result.x, [1, 2, 3, 4, 5])
        self.assertEqual(result.name, "wave")

        # SobelFilter
        w = Wave([1, 2, 3, 4, 5], [1, 2, 3, 4, 5], name="wave")
        f = filters.SobelFilter(axes=[0])
        f1 = filters.SobelFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [1, 2, 2, 2, 1])
        assert_array_equal(result.x, [1, 2, 3, 4, 5])
        self.assertEqual(result.name, "wave")

        # LaplacianFilter
        w = Wave([1, 2, 3, 4, 5], [1, 2, 3, 4, 5], name="wave")
        f = filters.LaplacianConvFilter(axes=[0])
        f1 = filters.LaplacianConvFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [1, 0, 0, 0, -1])
        assert_array_equal(result.x, [1, 2, 3, 4, 5])
        self.assertEqual(result.name, "wave")

    def test_dask(self):
        w = DaskWave(np.ones([100, 100]))
        f = filters.RechunkFilter(chunks=(50, 50))
        f1 = filters.RechunkFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f.execute(w)
        self.assertEqual(result.data.chunks, ((50, 50), (50, 50)))

    def test_differentiate(self):
        # GradientFilter
        w = Wave([1, 2, 3, 4, 5], [1, 2, 3, 4, 5], name="wave")
        f = filters.GradientFilter(axes=[0])
        f1 = filters.GradientFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [1, 1, 1, 1, 1])
        assert_array_equal(result.x, [1, 2, 3, 4, 5])
        self.assertEqual(result.name, "wave")

        # NablaFilter
        ar = np.array([1, 2, 3])
        w = Wave([ar + i for i in range(3)], ar, ar, name="wave")
        f = filters.NablaFilter()
        f1 = filters.NablaFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 1)
        result = f1.execute(w)
        assert_array_equal(result.data, np.ones([2, 3, 3]))
        self.assertFalse(result.axisIsValid(0))
        assert_array_equal(result.y, ar)
        self.assertEqual(result.name, "wave")

        # NablaFilter
        x = np.linspace(0, 100, 100)
        w = Wave(x**2, x, name="wave")
        f = filters.LaplacianFilter()
        f1 = filters.LaplacianFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, np.gradient(np.gradient(x**2, x), x))
        self.assertEqual(result.name, "wave")

    def test_freeline(self):
        w = Wave([[1, 2, 3], [2, 3, 4], [3, 4, 5]], [1, 2, 3], [1, 2, 3], name="wave")
        f = filters.FreeLineFilter(axes=[0, 1], range=[(1, 3), (2, 2)], width=1)
        f1 = filters.FreeLineFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), -1)
        result = f1.execute(w)
        assert_array_equal(result.data, [2, 3, 4])
        assert_array_equal(result.x, [0, 1, 2])
        self.assertEqual(result.name, "wave")

        f2 = filters.FreeLineFilter(axes=[0, 1], range=[(1, 3), (1, 3)], width=1)
        result = f2.execute(w)
        assert_array_equal(result.data, [1, 3, 5])
        assert_array_equal(result.x, [0, np.sqrt(2), 2 * np.sqrt(2)])

    def test_freqency(self):
        # prepare data
        x = np.linspace(0, 100, 100)
        w = Wave(x, x, name="wave")

        # LowPassFilter
        f = filters.LowPassFilter(order=3, cutoff=0.1, axes=[0])
        f1 = filters.LowPassFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        b, a = signal.butter(3, 0.1)
        assert_array_equal(result.data, signal.filtfilt(b, a, w.data))
        assert_array_equal(result.x, x)
        self.assertEqual(result.name, "wave")

        # HighPassFilter
        f = filters.HighPassFilter(order=3, cutoff=0.1, axes=[0])
        f1 = filters.HighPassFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        b, a = signal.butter(3, 0.1, btype="highpass")
        assert_array_equal(result.data, signal.filtfilt(b, a, w.data))
        assert_array_equal(result.x, x)
        self.assertEqual(result.name, "wave")

        # BandPassFilter
        f = filters.BandPassFilter(order=3, cutoff=[0.1, 0.3], axes=[0])
        f1 = filters.BandPassFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        b, a = signal.butter(3, [0.1, 0.3], btype="bandpass")
        assert_array_equal(result.data, signal.filtfilt(b, a, w.data))
        assert_array_equal(result.x, x)
        self.assertEqual(result.name, "wave")

        # BandStopFilter
        f = filters.BandStopFilter(order=3, cutoff=[0.1, 0.3], axes=[0])
        f1 = filters.BandStopFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        b, a = signal.butter(3, [0.1, 0.3], btype="bandstop")
        assert_array_equal(result.data, signal.filtfilt(b, a, w.data))
        assert_array_equal(result.x, x)
        self.assertEqual(result.name, "wave")

        # check original wave is not modified
        assert_array_equal(w.data, x)

    def test_fft(self):
        w = Wave(np.ones([3, 3]), [0, 1, 2], [0, 1, 2], name="wave")
        f = filters.FourierFilter(axes=[0, 1])
        f1 = filters.FourierFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        ans = np.zeros([3, 3])
        ans[1, 1] = 9
        assert_array_equal(result.data, ans)
        assert_array_equal(result.x, [-0.75, 0, 0.75])
        self.assertEqual(result.name, "wave")

    def test_integral(self):
        # IntegralAllFilter
        w = Wave(np.ones([3, 4]), [1, 2, 3], [1, 2, 3, 4], name="wave")
        f = filters.IntegralAllFilter(axes=[0], sumtype="Sum")
        f1 = filters.IntegralAllFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), -1)
        result = f1.execute(w)
        assert_array_equal(result.data, [3, 3, 3, 3])
        assert_array_equal(result.x, [1, 2, 3, 4])
        self.assertEqual(result.name, "wave")

        # IntegralFilter
        w = Wave(np.ones([5, 5, 5]), [1, 2, 3, 4, 5], [1, 2, 3, 4, 5], [2, 3, 4, 5, 6], name="wave")
        f = filters.IntegralFilter([(1, 4), (2, 4), (0, 0)], sumtype="Sum")
        f1 = filters.IntegralFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), -2)
        result = f1.execute(w)
        assert_array_equal(result.data, [6, 6, 6, 6, 6])
        assert_array_equal(result.x, [2, 3, 4, 5, 6])
        self.assertEqual(result.name, "wave")

        # IntegralCircleFilter TODO

    def test_interp(self):
        # InterpFilter
        x = np.linspace(0, 100, 100)
        w = Wave(x**2, x, name="wave")
        f = filters.InterpFilter(size=(200,))
        f1 = filters.InterpFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_almost_equal(result.data, result.x**2)
        assert_array_equal(result.x, np.linspace(0, 100, 200))
        self.assertEqual(result.name, "wave")

    def test_index(self):
        # SelectIndexFilter
        w = Wave([[1, 2, 3], [4, 5, 6]], [7, 8], [9, 10, 11], name="wave")
        f = filters.SelectIndexFilter(axis=0, index=1)
        f1 = filters.SelectIndexFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), -1)
        result = f1.execute(w)
        assert_array_equal(result.data, [4, 5, 6])
        assert_array_equal(result.x, [9, 10, 11])
        self.assertEqual(result.name, "wave")

        # SliceFilter
        w = Wave([[1, 2, 3], [4, 5, 6]], [7, 8], [9, 10, 11], name="wave")
        f = filters.SliceFilter([slice(None), slice(1, 3)])
        f1 = filters.SliceFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), -1)
        result = f1.execute(w)
        assert_array_equal(result.data, [[2, 3], [5, 6]])
        assert_array_equal(result.x, [7, 8])
        assert_array_equal(result.y, [10, 11])
        self.assertEqual(result.name, "wave")

        # IndexMathFilter
        w = Wave([[1, 2, 3], [4, 5, 6]], [7, 8], [9, 10, 11], name="wave")
        f = filters.IndexMathFilter(axis=0, type="+", index1=0, index2=1)
        f1 = filters.IndexMathFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), -1)
        result = f1.execute(w)
        assert_array_equal(result.data, [5, 7, 9])
        assert_array_equal(result.x, [9, 10, 11])
        self.assertEqual(result.name, "wave")

        # TranposeFilter
        data = np.array([[1, 2, 3], [4, 5, 6]])
        w = Wave(data, [7, 8], [9, 10, 11], name="wave")
        f = filters.TransposeFilter(axes=[1, 0])
        f1 = filters.TransposeFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, data.T)
        assert_array_equal(result.x, [9, 10, 11])
        self.assertEqual(result.name, "wave")
