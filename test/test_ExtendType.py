import unittest
import shutil
import os
import warnings
from lys import load, filters, glb, home, Graph, errors


class ExtendType_test(unittest.TestCase):
    path = "test/DataFiles"

    def setUp(self):
        if glb.mainWindow() is None:
            if os.path.exists(home() + "/.lys"):
                shutil.rmtree(home() + "/.lys")
            glb.createMainWindow(show=False, restore=True)
        warnings.simplefilter("ignore", errors.NotSupportedWarning)

    def test_ExtendType(self):
        # load old type Wave
        w = load(self.path + "/oldwave.npz")
        self.assertEqual(w.data[0][0], 0.03680204736086041)
        self.assertEqual(w.x[0], 0)

        # load old type filter
        f = filters.fromFile(self.path + "/oldfilter.fil")
        self.assertEqual(f.getRelativeDimension(), -2)

        # load old type graph
        g = load(self.path + "/oldgraph1.grf")
        self.assertEqual(type(g), Graph)
