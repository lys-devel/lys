import unittest
import shutil
import os
import warnings
import numpy as np


from lys import glb, home, errors, Wave, edit
from lys.widgets import lysTable
from numpy.testing import assert_array_equal


class Graph_test(unittest.TestCase):
    path = "test/testData"

    def setUp(self):
        os.makedirs(self.path, exist_ok=True)
        warnings.simplefilter("ignore", errors.NotSupportedWarning)
        if glb.mainWindow() is None:
            if os.path.exists(home() + "/.lys"):
                shutil.rmtree(home() + "/.lys")
            glb.createMainWindow(show=False, restore=True)

    def tearDown(self):
        shutil.rmtree(self.path)

    def test_Table(self):
        w = Wave(np.random.rand(100))
        t = edit(w)
        d = t.saveAsDictionary()
        t2 = edit(Wave(np.random.rand(50)))
        t2.loadFromDictionary(d)
        assert_array_equal(t.getData().data, t2.getData().data)

    def test_Data(self):
        t = lysTable()

        # 1D data
        w = Wave(np.random.rand(100))
        t.setData(w)
        d = t.getData()

        assert_array_equal(d.data, w.data)
        assert_array_equal(d.axes[0], w.getAxis(0))
        t.setSlice()
        assert_array_equal(t.getSlicedData(), w.data)
        t.setSlice(0)
        assert_array_equal(t.getSlicedData(), w.getAxis(0))

        # 2D data
        w = Wave(np.random.rand(100, 100))
        t.setData(w)
        d = t.getData()

        assert_array_equal(d.data, w.data)
        assert_array_equal(d.axes[0], w.getAxis(0))
        assert_array_equal(d.axes[1], w.getAxis(1))
        t.setSlice()
        assert_array_equal(t.getSlicedData(), w.data)
        t.setSlice(0)
        assert_array_equal(t.getSlicedData(), w.getAxis(0))
        t.setSlice(1)
        assert_array_equal(t.getSlicedData(), w.getAxis(1))

        # 3D data
        w = Wave(np.random.rand(100, 100, 100))
        t.setData(w)
        d = t.getData()

        assert_array_equal(d.data, w.data)
        assert_array_equal(d.axes[0], w.getAxis(0))
        assert_array_equal(d.axes[1], w.getAxis(1))
        assert_array_equal(d.axes[2], w.getAxis(2))
        t.setSlice()
        assert_array_equal(t.getSlicedData(), w.data[:, :, 0])
        t.setSlice([slice(None), 1, slice(None)])
        assert_array_equal(t.getSlicedData(), w.data[:, 1, :])
        t.setSlice(0)
        assert_array_equal(t.getSlicedData(), w.getAxis(0))
        t.setSlice(1)
        assert_array_equal(t.getSlicedData(), w.getAxis(1))
        t.setSlice(2)
        assert_array_equal(t.getSlicedData(), w.getAxis(2))

        # save
        w = Wave(np.random.rand(100))
        t.setData(w)
        d = t.getData()
        d.data[0] = 1
        t.save()
        self.assertEqual(w.data[0], 1)

        # file
        w = Wave(np.random.rand(100))
        w.export(self.path + "/table.npz")
        t.setData(self.path + "/table.npz")
        d = t.getData()
        d.data[0] = 1
        t.save()
        w2 = Wave(self.path + "/table.npz")
        self.assertEqual(w2.data[0], 1)
