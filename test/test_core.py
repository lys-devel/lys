import unittest
import os
import shutil
from ExtendAnalysis.core import SettingDict


class core_test(unittest.TestCase):
    path = "test/testData"

    def setUp(self):
        os.mkdir(self.path)

    def tearDown(self):
        shutil.rmtree(self.path)

    def test_SettingDict(self):
        d = SettingDict()
        d["test1"] = "test1"
        d.Save(self.path + "/test.dic")

        d2 = SettingDict(self.path + "/test.dic")
        self.assertEqual(d2["test1"], "test1")
        d2["test1"] = "test2"

        d3 = SettingDict(self.path + "/test.dic")
        self.assertEqual(d3["test1"], "test2")
