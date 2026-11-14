import unittest

from tira_app.endpoints.admin_api import _evaluation_queue


class TestEvaluationQueue(unittest.TestCase):
    def test_absent_queue_keeps_existing_value(self):
        self.assertIsNone(_evaluation_queue({}))

    def test_queue_is_returned(self):
        self.assertEqual("my-queue", _evaluation_queue({"evaluation_queue": "my-queue"}))

    def test_empty_queue_resets_to_default(self):
        self.assertEqual("", _evaluation_queue({"evaluation_queue": ""}))

    def test_queue_with_whitespace_is_rejected(self):
        with self.assertRaises(ValueError):
            _evaluation_queue({"evaluation_queue": "my queue"})
