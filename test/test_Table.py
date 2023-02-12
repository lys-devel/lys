import unittest
import shutil
import os
import warnings


from lys import glb, home, errors, lysTable
from numpy.testing import assert_array_equal, assert_array_almost_equal


class Graph_test(unittest.TestCase):
    path = "test/DataFiles"

    def setUp(self):
        warnings.simplefilter("ignore", errors.NotSupportedWarning)
        if glb.mainWindow() is None:
            if os.path.exists(home() + "/.lys"):
                shutil.rmtree(home() + "/.lys")
            glb.createMainWindow(show=False, restore=True)

    def test_Area(self):
        d = {}
        c = g.canvas

        # set/get margin
        c.setMargin(0, 0, 0, 0)
        self.assertEqual(c.getMargin(raw=True), [0, 0, 0, 0])
        self.assertEqual(c.getMargin(), [0.2, 0.85, 0.2, 0.85])

        # save and load
        c.SaveAsDictionary(d)
        self.assertEqual(d["Margin"], [0, 0, 0, 0])
        c.setMargin(0.1, 0.1, 0.1, 0.1)
        c.LoadFromDictionary(d)
        self.assertEqual(c.getMargin(raw=True), [0, 0, 0, 0])
        self.assertEqual(c.getMargin(), [0.2, 0.85, 0.2, 0.85])

        # set/get area mode
        c.setCanvasSize("Both", "Absolute", 4)
        assert_array_almost_equal(c.getCanvasSize(), [4, 4])
        c.setCanvasSize("Height", "Aspect", 0.5)
        assert_array_almost_equal(c.getCanvasSize(), [4, 2])
        c.setCanvasSize("Both", "Absolute", 4)
        c.setCanvasSize("Width", "Aspect", 0.5)
        assert_array_almost_equal(c.getCanvasSize(), [2, 4])

        # save and load
        c.SaveAsDictionary(d)
        self.assertEqual(d["Size"]["Height"][0], "Absolute")
        self.assertAlmostEqual(d["Size"]["Height"][1], 4)
        self.assertEqual(d["Size"]["Width"][0], "Aspect")
        self.assertAlmostEqual(d["Size"]["Width"][1], 0.5)
        c.LoadFromDictionary(d)
        assert_array_almost_equal(c.getCanvasSize(), [2, 4])
