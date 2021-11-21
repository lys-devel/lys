import unittest
import shutil
import os

from lys import glb, home, Graph
from numpy.testing import assert_array_equal, assert_array_almost_equal


class Graph_test(unittest.TestCase):
    path = "test/DataFiles"

    def setUp(self):
        if glb.mainWindow() is None:
            if os.path.exists(home() + "/.lys"):
                shutil.rmtree(home() + "/.lys")
            glb.createMainWindow(show=False, restore=True)
        self.graphs = [Graph(lib=lib) for lib in ["matplotlib", "pyqtgraph"]]
        #self.graphs = [Graph(lib=lib) for lib in ["matplotlib"]]

    def test_Area(self):
        for g in self.graphs:
            d = {}
            c = g.canvas

            # set/get margin
            c.setMargin(0, 0, 0, 0)
            self.assertEqual(c.getMargin(raw=True), [0, 0, 0, 0])
            self.assertEqual(c.getMargin(), [0.2, 0.85, 0.2, 0.85])

            # save and load
            c.SaveAsDictionary(d, home())
            self.assertEqual(d["Margin"], [0, 0, 0, 0])
            c.setMargin(0.1, 0.1, 0.1, 0.1)
            c.LoadFromDictionary(d, home())
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
            c.SaveAsDictionary(d, home())
            self.assertEqual(d["Size"]["Height"][0], "Absolute")
            self.assertAlmostEqual(d["Size"]["Height"][1], 4)
            self.assertEqual(d["Size"]["Width"][0], "Aspect")
            self.assertAlmostEqual(d["Size"]["Width"][1], 0.5)
            c.LoadFromDictionary(d, home())
            assert_array_almost_equal(c.getCanvasSize(), [2, 4])

    def test_Axes(self):
        for g in self.graphs:
            d = {}
            c = g.canvas

            # axisIsValid
            self.assertTrue(c.axisIsValid("Left"))
            self.assertFalse(c.axisIsValid("Top"))

            # axisList
            self.assertEqual(c.axisList(), ["Left", 'Bottom'])

            # set/get
            c.setAxisRange("Left", [0, 1])
            c.setAxisRange("Bottom", [0, 2])
            assert_array_almost_equal(c.getAxisRange("Left"), (0, 1))
            assert_array_almost_equal(c.getAxisRange("Bottom"), (0, 2))

            self.assertFalse(c.isAutoScaled('Left'))
            self.assertFalse(c.isAutoScaled('Bottom'))

            # save and load
            c.SaveAsDictionary(d, home())
            assert_array_almost_equal(d["AxisRange"]["Left"], (0, 1))
            assert_array_almost_equal(d["AxisRange"]["Bottom"], (0, 2))
            self.assertFalse(d["AxisRange"]['Left_auto'])
            self.assertFalse(d["AxisRange"]['Bottom_auto'])
            c.setAxisRange("Left", [0, 2])
            c.setAxisRange("Bottom", [0, 1])
            c.LoadFromDictionary(d, home())
            assert_array_almost_equal(c.getAxisRange("Left"), (0, 1))
            assert_array_almost_equal(c.getAxisRange("Bottom"), (0, 2))

            # autoscale
            c.setAutoScaleAxis("Left")
            self.assertTrue(c.isAutoScaled("Left"))
            self.assertFalse(c.isAutoScaled("Bottom"))

            # signal
            c.b = False

            def dummy():
                c.b = True
            c.axisRangeChanged.connect(dummy)
            c.setAxisRange("Bottom", [0, 1])
            self.assertTrue(c.b)

            # thick
            c.setAxisThick('Left', 3)
            self.assertEqual(c.getAxisThick('Left'), 3)

            # color
            c.setAxisColor('Left', (0.5, 0.5, 0.5, 1))
            res = c.getAxisColor('Left')
            self.assertTrue(res == (0.5, 0.5, 0.5, 1) or res == "#7f7f7f")

            # mirror
            c.setMirrorAxis("Left", False)
            self.assertFalse(c.getMirrorAxis("Left"))

            # mode
            c.setAxisMode("Left", "linear")
            self.assertEqual(c.getAxisMode("Left"), "linear")

            # save and load
            c.SaveAsDictionary(d, home())
            self.assertEqual(d['AxisSetting']['Left_thick'], 3)
            res = d['AxisSetting']['Left_color']
            self.assertTrue(res == (0.5, 0.5, 0.5, 1) or res == "#7f7f7f")
            self.assertFalse(d['AxisSetting']['Left_mirror'])
            self.assertEqual(d['AxisSetting']['Left_mode'], 'linear')

            c.setAxisThick('Left', 4)
            c.setAxisColor('Left', (0, 0, 0, 1))
            c.setMirrorAxis("Left", True)

            c.LoadFromDictionary(d, home())
            self.assertEqual(c.getAxisThick('Left'), 3)
            res = c.getAxisColor('Left')
            self.assertTrue(res == (0.5, 0.5, 0.5, 1) or res == "#7f7f7f")
            self.assertFalse(c.getMirrorAxis("Left"))
            self.assertEqual(c.getAxisMode("Left"), "linear")
