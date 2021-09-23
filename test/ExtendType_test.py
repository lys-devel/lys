import unittest
import os
import shutil
import numpy as np
from ExtendAnalysis import *


class Wave_test(unittest.TestCase):
    path = "test/testData"

    def setUp(self):
        os.mkdir(self.path)

    def tearDown(self):
        shutil.rmtree(self.path)

    def test_AutoSaved(self):
        w1 = Wave()
        # None when failing initialization
        self.assertEqual(type(w1), Wave)

        # Set
        w1.data = [1, 2, 3]
        self.assertEqual(w1.data[1], 2)

        #Save and load
        w1.Save(self.path + "/wave1.npz")
        self.assertEqual(w1.IsConnected(), True)
        w1_2 = Wave(self.path + "/wave1.npz")
        self.assertEqual(w1_2.data[1], 2)

        #AutoSave and Sync
        w1.data = [2, 3, 4]
        self.assertEqual(w1.data[1], 3)
        self.assertEqual(w1_2.data[1], 3)

        # Disconnect
        w1.Disconnect()
        self.assertEqual(w1.IsConnected(), False)
        w1.data = [1, 2, 3]
        self.assertEqual(w1.data[1], 2)
        self.assertEqual(w1_2.data[1], 3)

        #FileName and Copy
        self.assertEqual(w1_2.FileName(), os.path.abspath(self.path + "/wave1.npz"))
        w1_2.Save(self.path + "/wave2.npz")
        self.assertEqual(w1_2.FileName(), os.path.abspath(self.path + "/wave2.npz"))

        # Reconnect to different file
        w1_3 = Wave(self.path + "/wave2.npz")
        w1_2.data = [1, 2, 3]
        w1_2.Save(self.path + "/wave3.npz")
        w1_2.data = [2, 3, 4]
        self.assertEqual(w1_2.data[1], 3)
        self.assertEqual(w1_3.data[1], 2)

        # Override
        w2 = Wave()
        w2.data = [1, 2, 3]
        w2.Save(self.path + "/wave3.npz")
        self.assertEqual(w1_2.data[1], 2)
        self.assertEqual(w2.data[1], 2)

    def test_Wave(self):
        w = Wave()

        w1 = Wave()
        w1.data = [1, 2, 3]
        self.assertTrue((w1.data == [1, 2, 3]).all())
        self.assertTrue((w1.x == [0, 1, 2]).all())
        self.assertTrue(w1.y is None)
        self.assertTrue(w1.z is None)
        self.assertTrue((w1.axes[0] == np.array(None)).all())

        w1.x = [1, 2, 3]
        self.assertTrue((w1.x == [1, 2, 3]).all())
        self.assertTrue((w1.axes[0] == [1, 2, 3]).all())

        w2 = Wave()
        w2.data = [[1, 2], [3, 4]]
        self.assertTrue((w2.data == [[1, 2], [3, 4]]).all())
        self.assertTrue((w2.x == [0, 1]).all())
        self.assertTrue((w2.y == [0, 1]).all())
        self.assertTrue(w2.z is None)

        w2.x = [1, 2]
        w2.y = [1, 2]
        self.assertTrue((w2.x == [1, 2]).all())
        self.assertTrue((w2.y == [1, 2]).all())
        self.assertTrue(w2.z is None)
