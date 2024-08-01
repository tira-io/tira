import unittest

from tira.io_utils import change_workdir_cmd


class ChangeWorkdirTest(unittest.TestCase):
    def test_none_returns_empty_chdir_cmd(self):
        expected = 'echo "did not change the working directory"'
        actual = change_workdir_cmd(None)

        self.assertEqual(actual, expected)

    def test_empty_string_returns_empty_chdir_cmd(self):
        expected = 'echo "did not change the working directory"'
        actual = change_workdir_cmd("")

        self.assertEqual(actual, expected)

    def test_string_with_only_whitespaces_returns_empty_chdir_cmd(self):
        expected = 'echo "did not change the working directory"'
        actual = change_workdir_cmd("    ")

        self.assertEqual(actual, expected)

    def test_string_with_non_absolute_foo_returns_empty_chdir_cmd(self):
        expected = 'echo "did not change the working directory"'
        actual = change_workdir_cmd("   hello world ")

        self.assertEqual(actual, expected)

    def test_string_correct_string_01(self):
        expected = 'cd /app; echo "changed workdir to /app"'
        actual = change_workdir_cmd("/app")

        self.assertEqual(actual, expected)

    def test_string_correct_string_02(self):
        expected = 'cd /app/; echo "changed workdir to /app/"'
        actual = change_workdir_cmd("/app/")

        self.assertEqual(actual, expected)

    def test_string_correct_string_03(self):
        expected = 'cd /app/; echo "changed workdir to /app/"'
        actual = change_workdir_cmd("/app/   ")

        self.assertEqual(actual, expected)

    def test_string_correct_string_04(self):
        expected = 'cd /hello/world; echo "changed workdir to /hello/world"'
        actual = change_workdir_cmd("   /hello/world ")

        self.assertEqual(actual, expected)
