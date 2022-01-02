import unittest
import shutil
import os
import warnings

from lys import glb, home, Wave, Graph, errors


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

    def test_CanvasBase(self):
        for g in self.graphs:
            d = {}
            c = g.canvas

            # append data
            data1d = Wave([1, 2, 3])
            data2d = Wave([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
            data2dc = Wave([[1 + 1j, 2 + 2j], [3 + 3j, 4 + 4j]])
            line = c.Append(data1d)
            image = c.Append(data2d)
            cont = c.Append(data2d, contour=True)
            rgb = c.Append(data2dc)
            # vec = c.Append(data2dc, vector=True)

            # get wave data
            self.assertEqual(len(c.getLines()), 1)
            self.assertEqual(len(c.getImages()), 1)
            self.assertEqual(len(c.getContours()), 1)
            self.assertEqual(len(c.getRGBs()), 1)
            self.assertEqual(len(c.getWaveData()), 4)
            #self.assertEqual(len(c.getVectorFields()), 1)

            c.SaveAsDictionary(d)

            # remove
            c.Remove(line)
            c.Remove(image)
            c.Remove(cont)
            c.Remove(rgb)

            self.assertEqual(len(c.getLines()), 0)
            self.assertEqual(len(c.getImages()), 0)
            self.assertEqual(len(c.getContours()), 0)
            self.assertEqual(len(c.getRGBs()), 0)

            # load
            c.LoadFromDictionary(d)
            self.assertEqual(len(c.getLines()), 1)
            self.assertEqual(len(c.getImages()), 1)
            self.assertEqual(len(c.getContours()), 1)
            self.assertEqual(len(c.getRGBs()), 1)

            c.Clear()
            self.assertEqual(len(c.getWaveData()), 0)

    def test_Line(self):
        for g in self.graphs:
            d = {}
            c = g.canvas

            line = c.Append(Wave([1, 2, 3]))
            line.setColor('#ff0000')
            self.assertEqual(line.getColor(), '#ff0000')

            line.setWidth(3)
            self.assertEqual(line.getWidth(), 3)

            line.setStyle("dashed")
            self.assertEqual(line.getStyle(), 'dashed')

            line.setMarker('circle')
            self.assertEqual(line.getMarker(), 'circle')

            line.setMarkerSize(5)
            self.assertEqual(line.getMarkerSize(), 5)

            line.setMarkerThick(3)
            self.assertEqual(line.getMarkerThick(), 3)

            line.setMarkerFilling('full')
            self.assertEqual(line.getMarkerFilling(), 'full')

            ap = line.saveAppearance()
            line.setColor('#ff00ff')
            line.setWidth(4)
            line.setStyle("solid")
            line.setMarker('nothing')
            line.setMarkerSize(3)
            line.setMarkerThick(2)
            line.setMarkerFilling('none')

            line.loadAppearance(ap)
            self.assertEqual(line.getWidth(), 3)
            self.assertEqual(line.getStyle(), 'dashed')
            self.assertEqual(line.getMarker(), 'circle')
            self.assertEqual(line.getMarkerSize(), 5)
            self.assertEqual(line.getMarkerThick(), 3)
            self.assertEqual(line.getMarkerFilling(), 'full')
