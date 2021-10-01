import unittest
import os
import shutil

import numpy as np

from lys import Wave, DaskWave, filters


class Filters_test(unittest.TestCase):
    path = "test/Filters"

    def setUp(self):
        os.makedirs(self.path, exist_ok=True)

    def tearDown(self):
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
        fs.saveAsFile(self.path + "/test.fil")
        loaded = filters.fromFile(self.path + "/test.fil")
        self.assertEqual(str(loaded), str(fs))

    def test_Integral(self):
        w = Wave(np.ones([3, 4]), [1, 2, 3], [1, 2, 3, 4])

        # IntegralAllFilter
        f = filters.IntegralAllFilter(axes=[0], sumtype="Sum")
        f1 = filters.IntegralAllFilter(**f.getParameters())
        self.assertEqual(f1.getRelativeDimension(), -1)
        result = f1.execute(w)
        self.assertTrue((result.data == [3, 3, 3, 3]).all())
