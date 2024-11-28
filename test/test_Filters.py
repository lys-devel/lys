import unittest
import os
import warnings
import shutil

import numpy as np
from scipy import signal

from numpy.testing import assert_array_equal, assert_array_almost_equal, assert_allclose

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

        # auto save in wave
        f2 = filters.fromWave(result1)
        self.assertEqual(str(f2), str(fs))

    def _check(self, f, w, data=None, x=None, y=None, decimal=7):
        f1 = type(f)(**f.getParameters())
        w.name = "wave"
        result = f1.execute(w)
        if data is not None:
            assert_array_almost_equal(result.data, data, decimal=decimal)
        if x is not None:
            assert_array_almost_equal(result.x, x, decimal=decimal)
        if y is not None:
            assert_array_almost_equal(result.y, y, decimal=decimal)
        self.assertEqual(result.name, w.name)
        self.assertEqual(result.ndim, w.ndim + f1.getRelativeDimension())
        return result

    def test_convolution(self):
        # PrewittFilter
        w = Wave([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
        f = filters.PrewittFilter(axes=[0])
        self._check(f, w, data=[1, 2, 2, 2, 1], x=[1, 2, 3, 4, 5])

        # SobelFilter
        f = filters.SobelFilter(axes=[0])
        self._check(f, w, data=[1, 2, 2, 2, 1], x=[1, 2, 3, 4, 5])

        # LaplacianFilter
        f = filters.LaplacianConvFilter(axes=[0])
        self._check(f, w, data=[1, 0, 0, 0, -1], x=[1, 2, 3, 4, 5])

    def test_dask(self):
        w = DaskWave(np.ones([100, 100]))
        f = filters.RechunkFilter(chunks=(50, 50))
        result = self._check(f, w)
        self.assertEqual(result.data.chunks, ((50, 50), (50, 50)))

    def test_differentiate(self):
        # GradientFilter
        w = Wave([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
        f = filters.GradientFilter(axes=[0])
        self._check(f, w, data=[1, 1, 1, 1, 1], x=[1, 2, 3, 4, 5])

        # NablaFilter
        ar = np.array([1, 2, 3])
        w = Wave([ar + i for i in range(3)], ar, ar)
        f = filters.NablaFilter()
        self._check(f, w, data=np.ones([2, 3, 3]), y=ar)

        # NablaFilter
        x = np.linspace(0, 100, 100)
        w = Wave(x**2, x)
        f = filters.LaplacianFilter()
        self._check(f, w, data=np.gradient(np.gradient(x**2, x), x))

    def test_freeline(self):
        w = Wave([[1, 2, 3], [2, 3, 4], [3, 4, 5]], [1, 2, 3], [1, 2, 3], name="wave")
        f = filters.FreeLineFilter(axes=[0, 1], range=[(1, 2), (3, 2)], width=1)
        self._check(f, w, data=[2, 3, 4], x=[0, 1, 2])

        f2 = filters.FreeLineFilter(axes=[0, 1], range=[(1, 1), (3, 3)], width=1)
        self._check(f2, w, data=[1, 3, 5], x=[0, np.sqrt(2), 2 * np.sqrt(2)])

    def test_freqency(self):
        # prepare data
        x = np.linspace(0, 100, 100)
        w = Wave(x, x)

        # LowPassFilter
        f = filters.LowPassFilter(order=3, cutoff=0.1, axes=[0])
        b, a = signal.butter(3, 0.1)
        self._check(f, w, data=signal.filtfilt(b, a, w.data), x=x)

        # HighPassFilter
        f = filters.HighPassFilter(order=3, cutoff=0.1, axes=[0])
        b, a = signal.butter(3, 0.1, btype="highpass")
        self._check(f, w, data=signal.filtfilt(b, a, w.data), x=x)

        # BandPassFilter
        f = filters.BandPassFilter(order=3, cutoff=[0.1, 0.3], axes=[0])
        b, a = signal.butter(3, [0.1, 0.3], btype="bandpass")
        self._check(f, w, data=signal.filtfilt(b, a, w.data), x=x)

        # BandStopFilter
        f = filters.BandStopFilter(order=3, cutoff=[0.1, 0.3], axes=[0])
        b, a = signal.butter(3, [0.1, 0.3], btype="bandstop")
        self._check(f, w, data=signal.filtfilt(b, a, w.data), x=x)

        # check original wave is not modified
        assert_array_equal(w.data, x)

    def test_fft(self):
        w = Wave(np.ones([3, 3]), [0, 1, 2], [0, 1, 2])
        f = filters.FourierFilter(axes=[0, 1])
        ans = np.zeros([3, 3])
        ans[1, 1] = 9
        self._check(f, w, data=ans, x=[-1 / 3, 0, 1 / 3])

    def test_integral(self):
        # IntegralAllFilter
        w = Wave(np.ones([3, 4]), [1, 2, 3], [1, 2, 3, 4])
        f = filters.IntegralAllFilter(axes=[0], sumtype="Sum")
        self._check(f, w, data=[3, 3, 3, 3], x=[1, 2, 3, 4])

        # IntegralFilter
        w = Wave(np.ones([5, 5, 5]), [1, 2, 3, 4, 5], [1, 2, 3, 4, 5], [2, 3, 4, 5, 6])
        f = filters.IntegralFilter([(1, 4), (2, 4), None], sumtype="Sum")
        self._check(f, w, data=[6, 6, 6, 6, 6], x=[2, 3, 4, 5, 6])

        # IntegralCircleFilter TODO

    def test_interp(self):
        # InterpFilter
        x = np.linspace(0, 100, 100)
        w = Wave(x**2, x)
        f = filters.InterpFilter(size=(200,))
        result = self._check(f, w, x=np.linspace(0, 100, 200))
        assert_array_almost_equal(result.data, result.x**2)

    def test_index(self):
        # SelectIndexFilter
        w = Wave([[1, 2, 3], [4, 5, 6]], [7, 8], [9, 10, 11])
        f = filters.SelectIndexFilter(axis=0, index=1)
        self._check(f, w, data=[4, 5, 6], x=[9, 10, 11])

        # SliceFilter
        f = filters.SliceFilter([slice(None), slice(1, 3)])
        self._check(f, w, data=[[2, 3], [5, 6]], x=[7, 8], y=[10, 11])

        # IndexMathFilter
        w = Wave([[1, 2, 3], [4, 5, 6]], [7, 8], [9, 10, 11])
        f = filters.IndexMathFilter(axis=0, type="+", index1=0, index2=1)
        self._check(f, w, data=[5, 7, 9], x=[9, 10, 11])

        # TranposeFilter
        data = np.array([[1, 2, 3], [4, 5, 6]])
        w = Wave(data, [7, 8], [9, 10, 11])
        f = filters.TransposeFilter(axes=[1, 0])
        self._check(f, w, data=data.T, x=[9, 10, 11])

    def test_region(self):
        # NormalizeFilter
        w = Wave(np.ones([5, 5]) * 2)
        f = filters.NormalizeFilter([(1, 4), (0, 0)], axis=[0])
        self._check(f, w, data=np.ones([5, 5]))

        # ReferenceNormalizeFilter
        f = filters.ReferenceNormalizeFilter(axis=1, type="Diff", refIndex=0)
        self._check(f, w, data=np.zeros([5, 5]))

        # ReferenceNormalizeFilter
        f = filters.ReferenceNormalizeFilter(axis=1, type="Divide", refIndex=0)
        self._check(f, w, data=np.ones([5, 5]))

        # SelectRegionFilter
        w = Wave(np.ones([5, 5]), [1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
        f = filters.SelectRegionFilter(range=[(2, 4), (1, 4)])
        self._check(f, w, data=np.ones([2, 3]), x=[2, 3], y=[1, 2, 3])

    def test_resize(self):
        # ReduceSizeFilter
        w = Wave(np.ones([6, 6]), [0, 1, 2, 3, 4, 5], [0, 1, 2, 3, 4, 5])
        f = filters.ReduceSizeFilter(kernel=(2, 2))
        self._check(f, w, data=np.ones([3, 3]), x=[0, 2, 4])

        # PaddingFilter
        w = Wave([1, 2, 3], [0, 1, 2])
        f = filters.PaddingFilter(axes=[0], value=0, size=2, position="first")
        self._check(f, w, data=[0, 0, 1, 2, 3], x=[-2, -1, 0, 1, 2])
        f = filters.PaddingFilter(axes=[0], value=0, size=2, position="last")
        self._check(f, w, data=[1, 2, 3, 0, 0], x=[0, 1, 2, 3, 4])
        f = filters.PaddingFilter(axes=[0], value=0, size=2, position="both")
        self._check(f, w, data=[0, 0, 1, 2, 3, 0, 0], x=[-2, -1, 0, 1, 2, 3, 4])

    def test_threshold(self):
        # Threshold
        w = Wave([[1, 1, 1], [1, 2, 1], [1, 1, 1]])
        f = filters.ThresholdFilter(threshold=1.5)
        self._check(f, w, data=[[np.nan] * 3, [np.nan, 1, np.nan], [np.nan] * 3])

        # AdaptiveThreshold
        f = filters.AdaptiveThresholdFilter(size=3, c=0.1)
        self._check(f, w, data=[[1, np.nan, 1], [np.nan, 1, np.nan], [1, np.nan, 1]])

    def test_shift(self):
        # Shift
        w = Wave([1, 2, 3], [1, 3, 5])
        f = filters.ShiftFilter(shift=[1])
        self._check(f, w, data=[0, 1.5, 2.5], x=[1, 3, 5])

        # Reverse
        f = filters.ReverseFilter(axes=[0])
        self._check(f, w, data=[3, 2, 1], x=[1, 3, 5])

        # Roll
        w = Wave([1, 2, 3, 4], [1, 2, 3, 4])
        f = filters.RollFilter(amount="1/2", axes=[0])
        self._check(f, w, data=[3, 4, 1, 2])

        # Reflect
        f = filters.ReflectFilter(type="first", axes=[0])
        self._check(f, w, data=[4, 3, 2, 1, 1, 2, 3, 4], x=[-3, -2, -1, 0, 1, 2, 3, 4])

        # Symmetrize
        w = Wave(np.random.rand(51, 51))
        f = filters.SymmetrizeFilter(rotation=4, center=[25, 25])
        result = self._check(f, w)
        assert_array_almost_equal(result.data, result.data[::-1, ::-1])

        # Mirror
        f = filters.MirrorFilter(positions=[(0, 0), (1, 1)])
        result = self._check(f, w)
        assert_array_almost_equal(result.data, result.data.T)

    def test_math(self):
        # simple math
        w = Wave([1, 2, 3], [1, 2, 3])
        f = filters.SimpleMathFilter(type="+", value=1)
        self._check(f, w, data=[2, 3, 4], x=[1, 2, 3])

        f = filters.SimpleMathFilter(type="-", value=1)
        self._check(f, w, data=[0, 1, 2], x=[1, 2, 3])

        f = filters.SimpleMathFilter(type="*", value=2)
        self._check(f, w, data=[2, 4, 6], x=[1, 2, 3])

        f = filters.SimpleMathFilter(type="/", value=2)
        self._check(f, w, data=[0.5, 1, 1.5], x=[1, 2, 3])

        # ComplexFilter
        w = Wave([1 + 2j, 2 + 3j, 3 + 4j], [1, 2, 3])
        f = filters.ComplexFilter(type="absolute")
        self._check(f, w, data=[np.sqrt(5), np.sqrt(13), 5], x=[1, 2, 3])

        f = filters.ComplexFilter(type="real")
        self._check(f, w, data=[1, 2, 3], x=[1, 2, 3])

        f = filters.ComplexFilter(type="imag")
        self._check(f, w, data=[2, 3, 4], x=[1, 2, 3])

        # PhaseFilter
        w = Wave([1, 1j], [1, 2])
        f = filters.PhaseFilter(rot=90)
        self._check(f, w, data=[1j, -1], x=[1, 2])

        # NanToNumFilter
        w = Wave([1, np.nan], [1, 2])
        f = filters.NanToNumFilter(value=0)
        self._check(f, w, data=[1, 0], x=[1, 2])

    def test_smooth(self):
        # MedianFilter
        w = Wave([1, 2, 1], [1, 2, 3])
        f = filters.MedianFilter(kernel=[2])
        self._check(f, w, data=[1, 2, 2], x=[1, 2, 3])

        # AverageFilter
        w = Wave([1, 2, 3], [1, 2, 3])
        f = filters.AverageFilter(kernel=[3])
        self._check(f, w, data=[1 + 1 / 3, 2, 2 + 2 / 3], x=[1, 2, 3])

        # GaussianFilter
        f = filters.GaussianFilter(kernel=[0.5])
        self._check(f, w, data=[1, 2, 2], x=[1, 2, 3])

    def test_axis(self):
        # SetAxisFilter
        w = Wave([1, 2, 3], [1, 2, 3])
        f = filters.SetAxisFilter(0, 0, 0.1, "step")
        self._check(f, w, data=[1, 2, 3], x=[0, 0.1, 0.2])

        # SetAxisFilter
        f = filters.SetAxisFilter(0, 0, 0.2, "stop")
        self._check(f, w, data=[1, 2, 3], x=[0, 0.1, 0.2])

        # ShiftAxisFilter
        f = filters.AxisShiftFilter(shift=[1], axes=[0])
        self._check(f, w, data=[1, 2, 3], x=[2, 3, 4])

        # MagnificationFilter
        f = filters.MagnificationFilter(mag=[2], axes=[0])
        self._check(f, w, data=[1, 2, 3], x=[1, 3, 5])

    def test_rotate(self):
        # Rotation2D
        w = Wave([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        f = filters.Rotation2DFilter(angle=90)
        self._check(f, w, data=[[3, 6, 9], [2, 5, 8], [1, 4, 7]])

        # Symmetrize
        f = filters.SymmetrizeFilter(rotation=90, center=(1, 1))
        self._check(f, w, data=np.ones([3, 3]) * 5)

    def test_drift(self):
        x, y = np.linspace(-10, 10, 200), np.linspace(-10, 10, 200)
        xx, yy = np.meshgrid(x,y)
        w = Wave([np.exp(-(xx ** 2 + yy**2)), np.exp(-((xx-2) ** 2 + (yy-3)**2)), np.exp(-((xx-3) ** 2 + (yy-4)**2))], None, x, y)

        f1 = filters.DriftCorrection((1,2), [(-10, 10), (-10, 10)], apply = False, method="Cross correlation")
        self._check(f1, w, data=[(0,0), (20,30), (30,40)])

        f1a = filters.DriftCorrection((1,2), [(-10, 10), (-10, 10)], method="Cross correlation")
        assert_allclose(f1a.execute(w).data[2, 50:150, 50:150], w.data[0, 50:150, 50:150], atol=0.1, rtol=0)

        f2 = filters.DriftCorrection((1,2), [(-10, 10), (-10, 10)], apply = False, method="Phase correlation")
        assert_allclose(f2.execute(w).data, [(0,0), (20,30), (30,40)], rtol=0, atol=1)

        f2a = filters.DriftCorrection((1,2), [(-10, 10), (-10, 10)], method="Phase correlation")
        assert_allclose(f2a.execute(w).data[2, 50:150, 50:150], w.data[0, 50:150, 50:150], atol=0.1, rtol=0)

        f1.execute(w).export(self.path+"/shift.npz")
        f3 = filters.DriftCorrection((1,2), self.path+"/shift.npz", apply=False, method="From file")
        self._check(f3, w, data=[(0,0), (20,30), (30,40)])

        f3a = filters.DriftCorrection((1,2), self.path+"/shift.npz", apply=True, method="From file")
        assert_allclose(f3a.execute(w).data[2, 50:150, 50:150], w.data[0, 50:150, 50:150], atol=0.1, rtol=0)
