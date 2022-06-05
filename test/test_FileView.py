import unittest
import os
import shutil
from pathlib import Path


from lys import home, glb
from lys.widgets.fileView import _moveFiles
from LysQt.QtWidgets import QAction, QMenu


class FileView_test(unittest.TestCase):
    path = "test/FileView"

    def setUp(self):
        if glb.mainWindow() is None:
            if os.path.exists(home() + "/.lys"):
                shutil.rmtree(home() + "/.lys")
            glb.createMainWindow(show=False, restore=True)
        os.makedirs(self.path, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.path)

    def test_moveFiles(self):
        file1 = Path(self.path + "/file1.txt")
        file1.write_text("file1")
        self.assertEqual(file1.read_text(), "file1")

        # copy
        file2 = Path(self.path + "/file2.txt")
        _moveFiles(file1, file2, copy=True)
        self.assertEqual(file1.read_text(), file2.read_text())

        # move
        file3 = Path(self.path + "/file3.txt")
        _moveFiles(file2, file3)
        self.assertFalse(file2.exists())
        self.assertEqual(file1.read_text(), file3.read_text())

        # rename
        _moveFiles(file3, file2)
        self.assertFalse(file3.exists())
        self.assertEqual(file1.read_text(), file2.read_text())

        # multicopy
        file4 = Path(self.path + "/file4.txt")
        file5 = Path(self.path + "/file5.txt")
        _moveFiles([file1, file2], [file4, file5])
        self.assertFalse(file1.exists())
        self.assertFalse(file2.exists())
        self.assertTrue(file4.exists())
        self.assertTrue(file5.exists())

    def test_FileSystemView(self):
        # selectedPaths
        view = glb.mainWindow().fileView
        self.assertEqual(view.selectedPaths()[0], home())
        self._flg1 = False

        # registerFileMenu
        def _change():
            self._flg1 = True
        menu = QMenu()
        action = QAction("Test", triggered=_change)
        menu.addAction(action)
        view.registerFileMenu("txt", menu)
        single = view._builder._test("txt_single").actions()[0]
        multi = view._builder._test("txt_multi").actions()[0]
        self.assertEqual(single.text(), "Test")
        self.assertEqual(multi.text(), "Test")
        single.trigger()
        self.assertTrue(self._flg1)
        self._flg1 = False
        multi.trigger()
        self.assertTrue(self._flg1)
