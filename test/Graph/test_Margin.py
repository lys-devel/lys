import unittest
import shutil
import os

from lys import glb, home, Graph


class Graph_test(unittest.TestCase):
    path = "test/DataFiles"

    def setUp(self):
        if glb.mainWindow() is None:
            if os.path.exists(home() + "/.lys"):
                shutil.rmtree(home() + "/.lys")
            glb.createMainWindow(show=False, restore=True)

    def test_Margin(self):
        for lib in ["matplotlib", "pyqtgraph"]:
            d = {}
            c = Graph(lib=lib).canvas

            # set/get margin
            c.margin.setMargin(0, 0, 0, 0)
            self.assertEqual(c.margin.getMargin(raw=True), [0, 0, 0, 0])
            self.assertEqual(c.margin.getMargin(), [0.2, 0.85, 0.2, 0.85])

            # save and load
            c.SaveAsDictionary(d, home())
            self.assertEqual(d["Margin"], [0, 0, 0, 0])
            c.margin.setMargin(0.1, 0.1, 0.1, 0.1)
            c.LoadFromDictionary(d, home())
            self.assertEqual(c.margin.getMargin(raw=True), [0, 0, 0, 0])
            self.assertEqual(c.margin.getMargin(), [0.2, 0.85, 0.2, 0.85])
