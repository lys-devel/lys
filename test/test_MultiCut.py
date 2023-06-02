import unittest
import numpy as np
from numpy.testing import assert_array_equal, assert_array_almost_equal

from lys import Wave, filters
from lys.mcut.MultiCutCUI import MultiCutCUI


class mcut_test(unittest.TestCase):
    def test_MultiCutWave(self):
        w = Wave(np.random.rand(100, 100))
        cui = MultiCutCUI(w)
        f = filters.MedianFilter([3, 3])

        self.value = 0

        def inc():
            self.value += 1

        cui.filterApplied.connect(inc)
        cui.applyFilter(f)
        self.assertEqual(self.value, 1)

        raw = cui.getRawWave().compute().data
        filt = cui.getFilteredWave().compute().data

        assert_array_almost_equal(raw, w.data)
        assert_array_almost_equal(filt, f.execute(w).data)

    def test_AxesRangeManager(self):
        w = Wave(np.random.rand(100, 100, 100), np.linspace(0, 10, 100), np.linspace(10, 20, 100), np.linspace(0, 30, 100))
        cui = MultiCutCUI(w)
        self.assertEqual(cui.getAxisRange(0), 0)
        self.assertEqual(cui.getAxisRange(1), 10)
        self.assertEqual(cui.getAxisRange(2), 0)

        cui.setAxisRange(0, (5, 7))
        cui.setAxisRange(1, [15, 17])
        cui.setAxisRange(2, 15)
        self.assertEqual(cui.getAxisRange(0), (5, 7))
        self.assertEqual(cui.getAxisRange(1), [15, 17])
        self.assertEqual(cui.getAxisRange(2), 15)

        self.assertEqual(cui.getAxisRangeType(0), "range")
        self.assertEqual(cui.getAxisRangeType(1), "range")
        self.assertEqual(cui.getAxisRangeType(2), "point")

        d = cui.saveAsDictionary(useRange=True)
        cui._axesRange.reset(w)
        self.assertEqual(cui.getAxisRange(0), 0)
        self.assertEqual(cui.getAxisRange(1), 10)
        self.assertEqual(cui.getAxisRange(2), 0)

        cui.loadFromDictionary(d, useRange=True)
        self.assertEqual(cui.getAxisRange(0), (5, 7))
        self.assertEqual(cui.getAxisRange(1), [15, 17])
        self.assertEqual(cui.getAxisRange(2), 15)

    def test_FreeLineManager(self):
        w = Wave(np.ones((100, 100, 100)), np.linspace(0, 10, 100), np.linspace(10, 20, 100), np.linspace(0, 30, 100))
        cui = MultiCutCUI(w)
        fline = cui.addFreeLine((0, 1), [(0, 5), (10, 15)], width=0.3)
        self.assertEqual(len(cui.getFreeLines()), 1)
        self.assertEqual(fline.getName(), "Line0")
        self.assertEqual(cui.getFreeLine("Line0"), fline)

        d = cui.saveAsDictionary(useLine=True)
        cui._freeLine.clear()
        self.assertEqual(len(cui.getFreeLines()), 0)
        cui.loadFromDictionary(d, useLine=True)
        self.assertEqual(cui.getFreeLine("Line0").getWidth(), 0.3)

    def test_ChildWaveManager(self):
        w = Wave(np.ones((101, 101, 101)), np.linspace(0, 10, 101), np.linspace(10, 20, 101), np.linspace(0, 30, 101))
        cui = MultiCutCUI(w)
        cui.setSumType("Sum")
        w1 = cui.addWave((0, 1))
        assert_array_almost_equal(w1.getFilteredWave().data, np.ones((101, 101)))
        self.assertEqual(w1.getRawWave().shape, (101, 101))

        cui.setAxisRange(2, (0, 15))
        assert_array_almost_equal(w1.getFilteredWave().data, np.ones((101, 101)) * 50)

        fline = cui.addFreeLine((0, 1), [(5, 11), (5, 13)], width=1)
        w2 = cui.addWave((2, fline.getName()))
        assert_array_almost_equal(w2.getFilteredWave().data, np.ones((101, 21)) * 10)
        fline.setWidth(2)
        assert_array_almost_equal(w2.getFilteredWave().data, np.ones((101, 21)) * 20)
