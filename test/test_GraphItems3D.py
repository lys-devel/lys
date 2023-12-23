import unittest
import shutil
import os
import warnings

import numpy as np

from lys import glb, home, Wave, display3D, errors, filters


class Graph3D_test(unittest.TestCase):
    path = "test/DataFiles"

    def setUp(self):
        warnings.simplefilter("ignore", errors.NotSupportedWarning)
        if glb.mainWindow() is None:
            if os.path.exists(home() + "/.lys"):
                shutil.rmtree(home() + "/.lys")
            glb.createMainWindow(show=False, restore=True)
        self._graph = display3D()

    def test_CanvasData(self):
        g = self._graph
        d = {}
        c = g.canvas

        # append data
        data_tetra = Wave([0]*4, [[0,0,0], [1,0,0], [0,1,0], [0,0,1]], elements={"tetra": [[0,1,2,3]]})
        data_hexa = Wave([0]*8, [[0,0,0], [1,0,0], [0,1,0], [1,1,0], [0,0,1], [1,0,1], [0,1,1], [1,1,1]], elements={"hexa": [[0,1,2,3,4,5,6,7]]})
        data_pyramid = Wave([0]*5, [[0,0,0], [1,0,0], [0,1,0], [1,1,0], [0,0,1]], elements={"pyramid": [[0,1,2,3,4]]})
        data_prism = Wave([0]*6, [[0,0,0], [1,0,0], [0,1,0], [0,0,1], [1,0,1], [0,1,1]], elements={"prism": [[0,1,2,3,4,5]]})
        data_triangle = Wave([0]*3, [[0,0,0], [1,0,0], [0,1,0]], elements={"triangle": [[0,1,2]]})
        data_quad = Wave([0]*4, [[0,0,0], [1,0,0], [0,1,0], [1,1,0]], elements={"quad": [[0,1,2,3]]})
        data_line = Wave([0]*2, [[0,0,0], [1,0,0]], elements={"line": [[0,1]]})
        data_point = Wave([0], [[0,0,0]], elements={"point": [[0]]})

        tetra = c.append(data_tetra)
        hexa = c.append(data_hexa)
        pyramid = c.append(data_pyramid)
        prism = c.append(data_prism)
        triangle = c.append(data_triangle)
        quad = c.append(data_quad)
        line = c.append(data_line)
        point = c.append(data_point)


        # get wave data
        self.assertEqual(len(c.getVolume()), 4)
        self.assertEqual(len(c.getSurface()), 2)
        self.assertEqual(len(c.getLine()), 1)
        self.assertEqual(len(c.getPoint()), 1)

        d = c.SaveAsDictionary()

        # remove
        c.remove(tetra)
        c.remove(triangle)
        c.remove(line)
        c.remove(point)

        self.assertEqual(len(c.getVolume()), 3)
        self.assertEqual(len(c.getSurface()), 1)
        self.assertEqual(len(c.getLine()), 0)
        self.assertEqual(len(c.getPoint()), 0)

        # load
        c.LoadFromDictionary(d)
        self.assertEqual(len(c.getVolume()), 4)
        self.assertEqual(len(c.getSurface()), 2)
        self.assertEqual(len(c.getLine()), 1)
        self.assertEqual(len(c.getPoint()), 1)

        c.clear()
        self.assertEqual(len(c.getWaveData()), 0)

    def test_WaveData3D(self):
        g = self._graph
        c = g.canvas

        data_triangle = Wave([0]*3, [[0,0,0], [1,0,0], [0,1,0]], elements={"triangle": [[0,1,2]]})

        obj = c.append(data_triangle)
        obj.setVisible(False)
        self.assertFalse(obj.getVisible())

        f = filters.SimpleMathFilter('+', 1)
        obj.setFilter(f)
        self.assertEqual(obj.getFilter(), f)

        d = c.SaveAsDictionary()
        obj.setVisible(True)

        c.LoadFromDictionary(d)
        obj = c.getSurface()[0]
        self.assertFalse(obj.getVisible())

    def test_Volume(self):
        g = self._graph
        c = g.canvas

        data_tetra = Wave([0]*4, [[0,0,0], [1,0,0], [0,1,0], [0,0,1]], elements={"tetra": [[0,1,2,3]]})
        obj = c.append(data_tetra)

        obj.showEdges(True)
        self.assertTrue(obj.edgesVisible())

        obj.showMeshes(True)
        self.assertTrue(obj.meshesVisible())        

        obj.setColor(color="#222222", type="color")
        self.assertEqual(obj.getColor(), "#222222")
        self.assertEqual(obj.getColorType(), "color")

        obj.setColor(color="gray", type="scalars")
        self.assertEqual(obj.getColor(), "gray")
        self.assertEqual(obj.getColorType(), "scalars")

        d = c.SaveAsDictionary()
        obj.showEdges(False)
        obj.showMeshes(False)
        obj.setColor(color="#222222", type="color")

        c.LoadFromDictionary(d)
        obj = c.getVolume()[0]
        self.assertTrue(obj.edgesVisible())
        self.assertTrue(obj.meshesVisible())        
        self.assertEqual(obj.getColor(), "gray")
        self.assertEqual(obj.getColorType(), "scalars")

    def test_Surface(self):
        g = self._graph
        c = g.canvas

        data_triangle = Wave([0]*3, [[0,0,0], [1,0,0], [0,1,0]], elements={"triangle": [[0,1,2]]})
        obj = c.append(data_triangle)

        obj.showEdges(True)
        self.assertTrue(obj.edgesVisible())

        obj.showMeshes(True)
        self.assertTrue(obj.meshesVisible())        

        obj.setColor(color="#222222", type="color")
        self.assertEqual(obj.getColor(), "#222222")
        self.assertEqual(obj.getColorType(), "color")

        obj.setColor(color="gray", type="scalars")
        self.assertEqual(obj.getColor(), "gray")
        self.assertEqual(obj.getColorType(), "scalars")

        d = c.SaveAsDictionary()
        obj.showEdges(False)
        obj.showMeshes(False)
        obj.setColor(color="#222222", type="color")

        c.LoadFromDictionary(d)
        obj = c.getSurface()[0]
        self.assertTrue(obj.edgesVisible())
        self.assertTrue(obj.meshesVisible())        
        self.assertEqual(obj.getColor(), "gray")
        self.assertEqual(obj.getColorType(), "scalars")

    def test_Line(self):
        g = self._graph
        c = g.canvas

        data_line = Wave([0]*2, [[0,0,0], [1,0,0]], elements={"line": [[0,1]]})
        obj = c.append(data_line)

        obj.showEdges(True)
        self.assertTrue(obj.edgesVisible())

        obj.showMeshes(True)
        self.assertTrue(obj.meshesVisible())        

        obj.setColor(color="#222222", type="color")
        self.assertEqual(obj.getColor(), "#222222")
        self.assertEqual(obj.getColorType(), "color")

        obj.setColor(color="gray", type="scalars")
        self.assertEqual(obj.getColor(), "gray")
        self.assertEqual(obj.getColorType(), "scalars")

        d = c.SaveAsDictionary()
        obj.showEdges(False)
        obj.showMeshes(False)
        obj.setColor(color="#222222", type="color")

        c.LoadFromDictionary(d)
        obj = c.getLine()[0]
        self.assertTrue(obj.edgesVisible())
        self.assertTrue(obj.meshesVisible())        
        self.assertEqual(obj.getColor(), "gray")
        self.assertEqual(obj.getColorType(), "scalars")
