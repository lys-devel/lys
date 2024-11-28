import unittest
import numpy as np

from lys.functions import load, loadableFiles, registerFileLoader


class functions_test(unittest.TestCase):
    path = "test/DataFiles"

    def test_load(self):
        # loadableFiles
        self.assertTrue(".npz" in loadableFiles())

        # registerFileLoader
        registerFileLoader(".txt", np.loadtxt)
        w = load(self.path + "/test.txt")
        self.assertEqual(w.data[0], 1)

        # load npz
        w = load(self.path + "/data1.npz")
        self.assertEqual(w.shape, (11, 11))
        self.assertEqual(w.data[0][0], 0)
        self.assertEqual(w.x[0], 0)
        self.assertEqual(w.y[0], 0)
        self.assertEqual(w.name, "data1")

        # load dic
        d = load(self.path + "/test.dic")
        self.assertEqual(d["data"], "test")
