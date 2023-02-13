import unittest
import os
import shutil
import warnings

from lys import glb, home, registerFileLoader, errors
from lys.Qt import QtWidgets
from lys.widgets import LysSubWindow, _ExtendMdiArea
from lys.widgets.mdi import _ConservableWindow


class testSubWindow(LysSubWindow):
    def __init__(self):
        super().__init__()
        self.spin = QtWidgets.QSpinBox(objectName="spin1")
        self.setWidget(self.spin)


class testAutoSavedWindow(_ConservableWindow):
    def __init__(self, file=None, **kwargs):
        super().__init__(file)
        if file is None:
            self.text = ""
        else:
            with open(file, "r") as f:
                self.text = f.read()

    def setText(self, txt):
        self.text = txt
        self.modified.emit()

    def _save(self, file):
        with open(file, "w") as f:
            f.write(self.text)

    def _prefix(self):
        return "text"

    def _suffix(self):
        return ".txt"


class FileView_test(unittest.TestCase):
    path = "test/MainWindow"

    def setUp(self):
        warnings.simplefilter("ignore", errors.NotSupportedWarning)
        os.makedirs(self.path, exist_ok=True)
        if glb.mainWindow() is None:
            if os.path.exists(home() + "/.lys"):
                shutil.rmtree(home() + "/.lys")
            glb.createMainWindow(show=False, restore=True)
        registerFileLoader(".txt", testAutoSavedWindow)

    def tearDown(self):
        shutil.rmtree(self.path)

    def test_LysSubWindow(self):
        win1 = testSubWindow()
        current = _ExtendMdiArea.current()
        self.assertTrue(win1 in current.subWindowList())
        win1.spin.setValue(1)
        win1.saveSettings(self.path + "/setting.dic")
        win1.close()

        win2 = testSubWindow()
        win2.restoreSettings(self.path + "/setting.dic")
        self.assertEqual(win2.spin.value(), 1)

        # functionalities related to motion of window is note tested.
        # resized, closed, moved signals, attach and attachTo methods.

    def test_AutoSavedWindow(self):
        win1 = testAutoSavedWindow()
        win1.setText("test1")
        self.assertEqual(win1.TemporaryFile(), home() + "/.lys/workspace/default/wins/text000.txt")

        win2 = testAutoSavedWindow()
        win2.setText("test2")
        win2.Save(self.path + "/text2.txt")
        self.assertEqual(win2.Name(), "test/MainWindow/text2.txt")

        _ExtendMdiArea.current().storeWorkspace()
        _ExtendMdiArea.current().restoreWorkspace()
