import unittest

from lys.glb import shell


class core_test(unittest.TestCase):
    def test_ExtendShell(self):
        s = shell()
        # exec, eval
        s.exec("a=1")
        self.assertEqual(s.eval("a"), 1)
        # importModule
        s.importModule("time")
        self.assertTrue(s.eval("time") is not None)
        s.importAll("time")
        self.assertTrue(s.eval("sleep") is not None)
        # addObject
        b = 1
        s.addObject(b, name="b", printResult=False)
        self.assertEqual(s.eval("b"), b)
