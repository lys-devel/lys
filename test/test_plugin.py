import unittest
import numpy as np

from ExtendAnalysis import load, plugin


class functions_test(unittest.TestCase):
    path = "test/DataFiles"

    def test_registerFileLoader(self):
        def loader(f): return np.loadtxt(f)
        plugin.registerFileLoader(".txt", loader)
        w = load(self.path + "/test.txt")
        self.assertEqual(w.data[0], 1)
