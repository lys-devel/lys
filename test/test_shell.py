import unittest

from ExtendAnalysis.plugin import shell


class core_test(unittest.TestCase):
    def test_ExtendShell(self):
        shell.exec("a=1")
        self.assertEqual(shell.eval("a"), 1)
        shell.importModule("time")
        self.assertTrue(shell.eval("time") is not None)
