import unittest

from ExtendAnalysis.functions import load, loadableFiles


class functions_test(unittest.TestCase):
    path = "test/DataFiles"

    def test_load(self):
        # loadableFiles
        self.assertTrue(".npz" in loadableFiles())

        # load npz
        w = load(self.path + "/data1.npz")
        self.assertEqual(w.shape, (11, 11))
        self.assertEqual(w.data[0][0], 0)
        self.assertEqual(w.x[0], 0)
        self.assertEqual(w.y[0], 0)
        self.assertEqual(w.name, "wave")

        # load png
        w2 = load(self.path + "/data1.png")
        self.assertTrue((w.data == w2.data).all())

        # load tif
        w2 = load(self.path + "/data1.tif")
        self.assertTrue((w.data == w2.data).all())

        # load jpg
        w2 = load(self.path + "/data1.jpg")
        self.assertEqual(w.shape, w2.shape)

        # load dic
        d = load(self.path + "/test.dic")
        self.assertEqual(d["data"], "test")
