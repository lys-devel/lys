import unittest
import numpy as np

from lys.fitting import fit


class fitting_test(unittest.TestCase):
    def test_fitting(self):
        x = [1, 2, 3, 4, 5]
        y = [1, 2, 3, 4, 5]
        c, sig = fit(lambda x, a, b: a * x + b, x, y)
        self.assertAlmostEqual(c[0], 1)
        self.assertAlmostEqual(c[1], 0)

        c, sig = fit([lambda x, a: a * x, lambda x, C: x * 0 + C], x, y)
        self.assertAlmostEqual(c[0], 1)
        self.assertAlmostEqual(c[1], 0)

        c, sig = fit(lambda x, a, b: a * x + b, x, y, bounds=np.array([(0, 0), (-np.inf, np.inf)]).T)
        self.assertAlmostEqual(c[0], 0)
        self.assertAlmostEqual(c[1], 3)
