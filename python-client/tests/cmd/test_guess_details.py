import unittest

from tira.tira_run import guess_system_details, guess_vm_id_of_user

from ..format_check import JSONL_OUTPUT_VALID


class TestGuessDetails(unittest.TestCase):
    def test_guess_vm_id_01(self):
        expected = "hello-world"
        actual = guess_vm_id_of_user(rest_client=None, tira_task_id=None, tira_vm_id="hello-world")
        self.assertEqual(expected, actual)

    def test_guess_vm_id_02(self):
        expected = "foo"
        actual = guess_vm_id_of_user(rest_client=None, tira_task_id=None, tira_vm_id="foo")
        self.assertEqual(expected, actual)

    def test_guess_system_details_01(self):
        expected = {"tag": "hello-world"}
        actual = guess_system_details(directory=None, system="hello-world")
        self.assertEqual(expected, actual)

    def test_guess_system_details_02(self):
        expected = {"tag": "foo"}
        actual = guess_system_details(directory=None, system="foo")
        self.assertEqual(expected, actual)

    def test_guess_system_details_03(self):
        actual = guess_system_details(
            directory=JSONL_OUTPUT_VALID.parent / "longeval-ir-metadata" / "ir-metadata.yml", system=None
        )
        self.assertEqual("ows_bm25_bo1_keyqueries", actual["tag"])
        self.assertIn("A keyquerey approach that reformulates", actual["description"])
