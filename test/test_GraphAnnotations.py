import unittest
import shutil
import os
import warnings

from lys import glb, home, Graph, errors


class Graph_test(unittest.TestCase):
    path = "test/DataFiles"

    def setUp(self):
        warnings.simplefilter("ignore", errors.NotSupportedWarning)
        if glb.mainWindow() is None:
            if os.path.exists(home() + "/.lys"):
                shutil.rmtree(home() + "/.lys")
            glb.createMainWindow(show=False, restore=True)
        self.graphs = [Graph(lib=lib) for lib in ["matplotlib", "pyqtgraph"]]
        #self.graphs = [Graph(lib=lib) for lib in ["matplotlib"]]

    def test_LineAnnotation(self):
        for g in self.graphs:
            c = g.canvas

            line = c.addLineAnnotation()
            line.setPosition([(0, 1), (2, 3)])
            self.assertEqual(line.getPosition(), [(0, 1), (2, 3)])

            line.setColor('#ff0000')
            self.assertEqual(line.getColor(), '#ff0000')

            line.setStyle('dashed')
            self.assertEqual(line.getStyle(), 'dashed')

            line.setWidth(3)
            self.assertEqual(line.getWidth(), 3)

            d = line.saveAppearance()
            line.setColor('#ff00ff')
            line.setStyle('solid')
            line.setWidth(4)

            line.loadAppearance(d)
            self.assertEqual(line.getColor(), '#ff0000')
            self.assertEqual(line.getStyle(), 'dashed')
            self.assertEqual(line.getWidth(), 3)

    def test_InfiniteLineAnnotation(self):
        for g in [self.graphs[1]]:
            c = g.canvas

            line = c.addInfiniteLineAnnotation()
            line.setPosition(5)
            self.assertEqual(line.getPosition(), 5)

            line.setColor('#ff0000')
            self.assertEqual(line.getColor(), '#ff0000')

            line.setStyle('dashed')
            self.assertEqual(line.getStyle(), 'dashed')

            line.setWidth(3)
            self.assertEqual(line.getWidth(), 3)

            d = line.saveAppearance()
            line.setColor('#ff00ff')
            line.setStyle('solid')
            line.setWidth(4)

            line.loadAppearance(d)
            self.assertEqual(line.getColor(), '#ff0000')
            self.assertEqual(line.getStyle(), 'dashed')
            self.assertEqual(line.getWidth(), 3)
