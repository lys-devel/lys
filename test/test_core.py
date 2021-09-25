import unittest
import os
import shutil
import numpy as np

from ExtendAnalysis.core import SettingDict, Wave


class core_test(unittest.TestCase):
    path = "test/testData"

    def setUp(self):
        os.mkdir(self.path)

    def tearDown(self):
        shutil.rmtree(self.path)

    def test_SettingDict(self):
        # check normal save
        d = SettingDict()
        d["test1"] = "test1"
        d.Save(self.path + "/test.dic")

        # check normal load
        d2 = SettingDict(self.path + "/test.dic")
        self.assertEqual(d2["test1"], "test1")

        # check automatic save
        d2["test1"] = "test2"
        d3 = SettingDict(self.path + "/test.dic")
        self.assertEqual(d3["test1"], "test2")

    def test_WaveAxes(self):
        # without specifing axes
        noaxes = Wave([[1, 2], [3, 4]])
        self.assertEqual(len(noaxes.axes), 2)
        self.assertTrue((noaxes.axes[0] == np.array(None)).all())
        self.assertTrue((noaxes.axes[1] == np.array(None)).all())

        # with specifing axes
        axis1, axis2 = [2, 3, 4], [2, 3]
        w = Wave(np.zeros([3, 2]), axis1, axis2)
        self.assertEqual(len(w.axes), 2)
        self.assertTrue((w.axes[0] == axis1).all())
        self.assertTrue((w.axes[1] == axis2).all())

        # invalid axes specified
        with self.assertRaises(TypeError):
            w = Wave(np.zeros([3, 2]), "aaa", [2, 3])

        # axisIsValid method
        self.assertFalse(noaxes.axes.axisIsValid(0))
        self.assertFalse(noaxes.axes.axisIsValid(1))
        self.assertTrue(w.axes.axisIsValid(0))
        self.assertTrue(w.axes.axisIsValid(1))

        # getAxis method
        self.assertTrue((noaxes.getAxis(0) == [0, 1]).all())
        self.assertTrue((w.getAxis(0) == axis1).all())

        # posToPoint method
        w = Wave(np.ones([3, 2]), [1, 2, 3], [3, 4, 5])
        self.assertTrue(w.posToPoint((2, 4)) == (1, 1))
        self.assertTrue(w.posToPoint((1, 2, 3), axis=0) == (0, 1, 2))
        self.assertTrue(w.posToPoint(2, axis=0) == 1)

        # pointToPos method
        w = Wave(np.ones([3, 2]), [1, 2, 3], [3, 4, 5])
        self.assertTrue(w.pointToPos((1, 1)) == (2, 4))
        self.assertTrue(w.pointToPos((0, 1, 2), axis=0) == (1, 2, 3))
        self.assertTrue(w.pointToPos(1, axis=0) == 2)
