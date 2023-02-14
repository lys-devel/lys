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
        f = filters.FreeLineFilter(axes=[0, 1], range=[(1, 2), (3, 2)], width=1)
        f1 = filters.FreeLineFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), -1)
        result = f1.execute(w)
        assert_array_equal(result.data, [2, 3, 4])
        assert_array_equal(result.x, [0, 1, 2])
        self.assertEqual(result.name, "wave")

        f2 = filters.FreeLineFilter(axes=[0, 1], range=[(1, 1), (3, 3)], width=1)
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
        assert_array_almost_equal(result.x, [-1 / 3, 0, 1 / 3])
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

    def test_region(self):
        # NormalizeFilter
        w = Wave(np.ones([5, 5]) * 2, name="wave")
        f = filters.NormalizeFilter([(1, 4), (0, 0)], axis=[0])
        f1 = filters.NormalizeFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, np.ones([5, 5]))
        self.assertEqual(result.name, "wave")

        # ReferenceNormalizeFilter
        w = Wave(np.ones([5, 5]) * 2, name="wave")
        f = filters.ReferenceNormalizeFilter(axis=1, type="Diff", refIndex=0)
        f1 = filters.ReferenceNormalizeFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, np.zeros([5, 5]))
        self.assertEqual(result.name, "wave")

        # ReferenceNormalizeFilter
        w = Wave(np.ones([5, 5]) * 2, name="wave")
        f = filters.ReferenceNormalizeFilter(axis=1, type="Divide", refIndex=0)
        f1 = filters.ReferenceNormalizeFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, np.ones([5, 5]))
        self.assertEqual(result.name, "wave")

        # SelectRegionFilter
        w = Wave(np.ones([5, 5]), [1, 2, 3, 4, 5], [1, 2, 3, 4, 5], name="wave")
        f = filters.SelectRegionFilter(range=[(2, 4), (1, 4)])
        f1 = filters.SelectRegionFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, np.ones([2, 3]))
        assert_array_equal(result.x, [2, 3])
        assert_array_equal(result.y, [1, 2, 3])
        self.assertEqual(result.name, "wave")

    def test_resize(self):
        # ReduceSizeFilter
        w = Wave(np.ones([6, 6]), [0, 1, 2, 3, 4, 5], [0, 1, 2, 3, 4, 5], name="wave")
        f = filters.ReduceSizeFilter(kernel=(2, 2))
        f1 = filters.ReduceSizeFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, np.ones([3, 3]))
        assert_array_equal(result.x, [0, 2, 4])
        self.assertEqual(result.name, "wave")

        # PaddingFilter
        w = Wave([1, 2, 3], [0, 1, 2], name="wave")
        f = filters.PaddingFilter(axes=[0], value=0, size=2, position="first")
        f1 = filters.PaddingFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [0, 0, 1, 2, 3])
        assert_array_equal(result.x, [-2, -1, 0, 1, 2])
        self.assertEqual(result.name, "wave")

        w = Wave([1, 2, 3], [0, 1, 2], name="wave")
        f = filters.PaddingFilter(axes=[0], value=0, size=2, position="last")
        f1 = filters.PaddingFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [1, 2, 3, 0, 0])
        assert_array_equal(result.x, [0, 1, 2, 3, 4])
        self.assertEqual(result.name, "wave")

        w = Wave([1, 2, 3], [0, 1, 2], name="wave")
        f = filters.PaddingFilter(axes=[0], value=0, size=2, position="both")
        f1 = filters.PaddingFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [0, 0, 1, 2, 3, 0, 0])
        assert_array_equal(result.x, [-2, -1, 0, 1, 2, 3, 4])
        self.assertEqual(result.name, "wave")

    def test_threshold(self):
        # Threshold
        w = Wave([[1, 1, 1], [1, 2, 1], [1, 1, 1]], name="wave")
        f = filters.ThresholdFilter(threshold=1.5)
        f1 = filters.ThresholdFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [[np.nan] * 3, [np.nan, 1, np.nan], [np.nan] * 3])
        self.assertEqual(result.name, "wave")

        # AdaptiveThreshold
        w = Wave([[1, 1, 1], [1, 2, 1], [1, 1, 1]], name="wave")
        f = filters.AdaptiveThresholdFilter(size=3, c=0.1)
        f1 = filters.AdaptiveThresholdFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [[1, np.nan, 1], [np.nan, 1, np.nan], [1, np.nan, 1]])
        self.assertEqual(result.name, "wave")

    def test_shift(self):
        # Shift
        w = Wave([1, 2, 3], [1, 3, 5], name="wave")
        f = filters.ShiftFilter(shift=[1])
        f1 = filters.ShiftFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [0, 1.5, 2.5])
        assert_array_equal(result.x, [1, 3, 5])
        self.assertEqual(result.name, "wave")

        # Reverse
        w = Wave([1, 2, 3], [1, 3, 5], name="wave")
        f = filters.ReverseFilter(axes=[0])
        f1 = filters.ReverseFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [3, 2, 1])
        assert_array_equal(result.x, [1, 3, 5])
        self.assertEqual(result.name, "wave")

        # Roll
        w = Wave([1, 2, 3, 4], name="wave")
        f = filters.RollFilter(amount="1/2", axes=[0])
        f1 = filters.RollFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [3, 4, 1, 2])
        self.assertEqual(result.name, "wave")

        # Reflect
        w = Wave([1, 2, 3, 4], [1, 2, 3, 4], name="wave")
        f = filters.ReflectFilter(type="first", axes=[0])
        f1 = filters.ReflectFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [4, 3, 2, 1, 1, 2, 3, 4])
        assert_array_equal(result.x, [-3, -2, -1, 0, 1, 2, 3, 4])
        self.assertEqual(result.name, "wave")

        # Symmetrize
        w = Wave(np.random.rand(51, 51), name="wave")
        f = filters.SymmetrizeFilter(rotation=4, center=[25, 25])
        f1 = filters.SymmetrizeFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_almost_equal(result.data, result.data[::-1, ::-1])
        self.assertEqual(result.name, "wave")

        # Mirror
        w = Wave(np.random.rand(51, 51), name="wave")
        f = filters.MirrorFilter(positions=[(0, 0), (1, 1)])
        f1 = filters.MirrorFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_almost_equal(result.data, result.data.T)
        self.assertEqual(result.name, "wave")

    def test_math(self):
        # simple math
        w = Wave([1, 2, 3], [1, 2, 3], name="wave")
        f = filters.SimpleMathFilter(type="+", value=1)
        f1 = filters.SimpleMathFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [2, 3, 4])
        assert_array_equal(result.x, [1, 2, 3])
        self.assertEqual(result.name, "wave")

        w = Wave([1, 2, 3], [1, 2, 3], name="wave")
        f = filters.SimpleMathFilter(type="-", value=1)
        f1 = filters.SimpleMathFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [0, 1, 2])
        assert_array_equal(result.x, [1, 2, 3])
        self.assertEqual(result.name, "wave")

        w = Wave([1, 2, 3], [1, 2, 3], name="wave")
        f = filters.SimpleMathFilter(type="*", value=2)
        f1 = filters.SimpleMathFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [2, 4, 6])
        assert_array_equal(result.x, [1, 2, 3])
        self.assertEqual(result.name, "wave")

        w = Wave([1, 2, 3], [1, 2, 3], name="wave")
        f = filters.SimpleMathFilter(type="/", value=2)
        f1 = filters.SimpleMathFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [0.5, 1, 1.5])
        assert_array_equal(result.x, [1, 2, 3])
        self.assertEqual(result.name, "wave")

        # ComplexFilter
        w = Wave([1 + 2j, 2 + 3j, 3 + 4j], [1, 2, 3], name="wave")
        f = filters.ComplexFilter(type="absolute")
        f1 = filters.ComplexFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_almost_equal(result.data, [np.sqrt(5), np.sqrt(13), 5])
        assert_array_almost_equal(result.x, [1, 2, 3])
        self.assertEqual(result.name, "wave")

        w = Wave([1 + 2j, 2 + 3j, 3 + 4j], [1, 2, 3], name="wave")
        f = filters.ComplexFilter(type="real")
        f1 = filters.ComplexFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_almost_equal(result.data, [1, 2, 3])
        assert_array_almost_equal(result.x, [1, 2, 3])
        self.assertEqual(result.name, "wave")

        w = Wave([1 + 2j, 2 + 3j, 3 + 4j], [1, 2, 3], name="wave")
        f = filters.ComplexFilter(type="imag")
        f1 = filters.ComplexFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_almost_equal(result.data, [2, 3, 4])
        assert_array_almost_equal(result.x, [1, 2, 3])
        self.assertEqual(result.name, "wave")

        # PhaseFilter
        w = Wave([1, 1j], [1, 2], name="wave")
        f = filters.PhaseFilter(rot=90)
        f1 = filters.PhaseFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_almost_equal(result.data, [1j, -1])
        assert_array_almost_equal(result.x, [1, 2])
        self.assertEqual(result.name, "wave")

        # NanToNumFilter
        w = Wave([1, np.nan], [1, 2], name="wave")
        f = filters.NanToNumFilter(value=0)
        f1 = filters.NanToNumFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [1, 0])
        assert_array_equal(result.x, [1, 2])
        self.assertEqual(result.name, "wave")

    def test_smooth(self):
        # MedianFilter
        w = Wave([1, 2, 1], [1, 2, 3], name="wave")
        f = filters.MedianFilter(kernel=[2])
        f1 = filters.MedianFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [1, 2, 2])
        assert_array_equal(result.x, [1, 2, 3])
        self.assertEqual(result.name, "wave")

        # AverageFilter
        w = Wave([1, 2, 3], [1, 2, 3], name="wave")
        f = filters.AverageFilter(kernel=[3])
        f1 = filters.AverageFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [1 + 1 / 3, 2, 2 + 2 / 3])
        assert_array_equal(result.x, [1, 2, 3])
        self.assertEqual(result.name, "wave")

        # GaussianFilter
        w = Wave([1, 2, 3], [1, 2, 3], name="wave")
        f = filters.GaussianFilter(kernel=[0.5])
        f1 = filters.GaussianFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [1, 2, 2])
        assert_array_equal(result.x, [1, 2, 3])
        self.assertEqual(result.name, "wave")

    def test_axis(self):
        # SetAxisFilter
        w = Wave([1, 2, 3], [1, 2, 3], name="wave")
        f = filters.SetAxisFilter(0, 0, 0.1, "step")
        f1 = filters.SetAxisFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [1, 2, 3])
        assert_array_equal(result.x, [0, 0.1, 0.2])
        self.assertEqual(result.name, "wave")

        # SetAxisFilter
        w = Wave([1, 2, 3], [1, 2, 3], name="wave")
        f = filters.SetAxisFilter(0, 0, 0.2, "stop")
        f1 = filters.SetAxisFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [1, 2, 3])
        assert_array_equal(result.x, [0, 0.1, 0.2])
        self.assertEqual(result.name, "wave")

        # ShiftAxisFilter
        w = Wave([1, 2, 3], [1, 2, 3], name="wave")
        f = filters.AxisShiftFilter(shift=[1], axes=[0])
        f1 = filters.AxisShiftFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [1, 2, 3])
        assert_array_equal(result.x, [2, 3, 4])
        self.assertEqual(result.name, "wave")

        # MagnificationFilter
        w = Wave([1, 2, 3], [1, 2, 3], name="wave")
        f = filters.MagnificationFilter(mag=[2], axes=[0])
        f1 = filters.MagnificationFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [1, 2, 3])
        assert_array_equal(result.x, [1, 3, 5])
        self.assertEqual(result.name, "wave")

    def test_rotate(self):
        # Rotation2D
        w = Wave([[1, 2, 3], [4, 5, 6], [7, 8, 9]], name="wave")
        f = filters.Rotation2DFilter(angle=90)
        f1 = filters.Rotation2DFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_equal(result.data, [[3, 6, 9], [2, 5, 8], [1, 4, 7]])
        self.assertEqual(result.name, "wave")

        # Symmetrize
        w = Wave([[1, 2, 3], [4, 5, 6], [7, 8, 9]], name="wave")
        f = filters.SymmetrizeFilter(rotation=90, center=(1, 1))
        f1 = filters.SymmetrizeFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), 0)
        result = f1.execute(w)
        assert_array_almost_equal(result.data, np.ones([3, 3]) * 5)
        self.assertEqual(result.name, "wave")
