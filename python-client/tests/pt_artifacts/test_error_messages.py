import unittest

from . import load_artifact


class TestErrorMessages(unittest.TestCase):
    def test_error_message_on_empty_path(self):
        with self.assertRaises(ValueError) as cnt:
            load_artifact("tira:")
        self.assertIn("Invalid tira url. I expected", str(cnt.exception))

    def test_error_message_on_dataset_that_does_not_exist(self):
        with self.assertRaises(ValueError) as cnt:
            load_artifact("tira:i-am-not/a-data/set")
        self.assertIn("could not find a ir-dataset", str(cnt.exception))

    def test_error_message_on_missing_approach_name(self):
        with self.assertRaises(ValueError) as cnt:
            load_artifact("tira:argsme/2020-04-01/touche-2021-task-1/does-not-exist")
        self.assertIn("have no team and/or approach", str(cnt.exception))

    def test_error_message_on_missing_approach_name_02(self):
        with self.assertRaises(ValueError) as cnt:
            load_artifact("tira:argsme/2020-04-01/touche-2021-task-1/does-not-exist/a/b/c")
        self.assertIn("have no team and/or approach", str(cnt.exception))

    def test_error_message_for_non_existing_approach(self):
        with self.assertRaises(ValueError) as cnt:
            load_artifact("tira:argsme/2020-04-01/touche-2021-task-1/does-not-exist/does-not-exist")
        self.assertIn("No submission 'does-not-exist' by team 'does-not-exist' is publicly", str(cnt.exception))
