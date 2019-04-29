import unittest

from ExtendType_test import *
from GraphWindow_test import *


def suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(Wave_test))
  suite.addTest(unittest.makeSuite(Graph_test))
  return suite

if __name__ == '__main__':
  runner = unittest.TextTestRunner()
  test_suite = suite()
  runner.run(test_suite)
