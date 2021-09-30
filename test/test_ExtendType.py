import unittest

from lys import load


class ExtendType_test(unittest.TestCase):
    path = "test/DataFiles"

    def test_ExtendType(self):
        # load old type Wave
        w = load(self.path + "/oldwave.npz")
        self.assertEqual(w.data[0][0], 0.03680204736086041)
        self.assertEqual(w.x[0], 0)
