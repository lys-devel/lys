import unittest
import shutil

from lys import load, filters, glb, home, Graph


class ExtendType_test(unittest.TestCase):
    path = "test/DataFiles"

    def setUp(self):
        if glb.mainWindow() is None:
            shutil.rmtree(home() + "/.lys")
            glb.createMainWindow(show=False)

    def test_ExtendType(self):
        # load old type Wave
        w = load(self.path + "/oldwave.npz")
        self.assertEqual(w.data[0][0], 0.03680204736086041)
        self.assertEqual(w.x[0], 0)

        # load old type filter
        f = filters.fromFile(self.path + "/oldfilter.fil")
        self.assertEqual(f.getRelativeDimension(), -2)

        # load old type graph
        g = load(self.path + "/oldgraph.fil")
        self.assertEqual(type(g), Graph)
