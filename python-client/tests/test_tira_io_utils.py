import unittest

from tira.io_utils import extract_volume_mounts


class TestTiraIoUtils(unittest.TestCase):
    def test_simple_case_01(self):
        a, b, c = extract_volume_mounts("a:b:c")
        self.assertEqual("a", a)
        self.assertEqual("b", b)
        self.assertEqual("c", c)

    def test_simple_case_02(self):
        a, b, c = extract_volume_mounts("/workspace/tira/python-client:/foo:ro")
        self.assertEqual("/workspace/tira/python-client", a)
        self.assertEqual("/foo", b)
        self.assertEqual("ro", c)

    def test_windows_case_01(self):
        a, b, c = extract_volume_mounts("c:\\Windows:b:c")
        self.assertEqual("c:\\Windows", a)
        self.assertEqual("b", b)
        self.assertEqual("c", c)

    def test_windows_case_02(self):
        a, b, c = extract_volume_mounts("c:\\Windows:/foo:ro")
        self.assertEqual("c:\\Windows", a)
        self.assertEqual("/foo", b)
        self.assertEqual("ro", c)
