import unittest

from lys import glb


class global_test(unittest.TestCase):
    path = "test/DataFiles"

    def setUp(self):
        if glb.mainWindow() is None:
            if os.path.exists(home() + "/.lys"):
                shutil.rmtree(home() + "/.lys")
            glb.createMainWindow(show=False, restore=True)

    def test_mainAndShell(self):
        main = glb.mainWindow()
        self.assertTrue(main is not None)
        shell = glb.shell()
        self.assertTrue(shell is not None)
