import os
import sys
import unittest

from tira.io_utils import MonitoredExecution


class TestRunMonitoredCmd(unittest.TestCase):
    def test_command_without_exception(self):
        def my_command(_):
            print("hello stdout 1", file=sys.stdout)
            print("hello stderr 1", file=sys.stderr)
            print("hello stdout 2", file=sys.stdout)

        actual = MonitoredExecution().run(my_command)
        self.assertTrue((actual / "output").exists())
        self.assertEqual(0, len(os.listdir(actual / "output")))
        stdout = (actual / "stdout.txt").read_text()
        stderr = (actual / "stderr.txt").read_text()

        self.assertIn("hello stdout 2", stdout)
        self.assertIn("hello stderr 1", stderr)

    def test_command_with_exception(self):
        def my_command(_):
            print("stdout 1", file=sys.stdout)
            print("stderr 1", file=sys.stderr)
            raise ValueError("foo")

        actual = MonitoredExecution().run(my_command)
        self.assertTrue((actual / "output").exists())
        self.assertEqual(0, len(os.listdir(actual / "output")))
        stdout = (actual / "stdout.txt").read_text()
        stderr = (actual / "stderr.txt").read_text()

        self.assertIn("stdout 1", stdout)
        self.assertIn("stderr 1", stderr)
