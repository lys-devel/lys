import unittest, time
from ExtendAnalysis import *

class Graph_test(unittest.TestCase):
    def setUp(self):
        makeMainWindow()
    def test_Graph(self):
        g=Graph()
        c=g.canvas
