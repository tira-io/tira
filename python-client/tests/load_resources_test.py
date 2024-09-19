import unittest

from approvaltests import verify_as_json

from tests.test_utils import digest_of_resource


class TestLoadResources(unittest.TestCase):
    def test_redirects_in_incubator(self):
        actual = digest_of_resource("Passage_ANCE_FirstP_Checkpoint.zip")
        verify_as_json(actual)

    def test_redirects_in_incubator_for_stanford_lemmatiser(self):
        actual = digest_of_resource("custom-terrier-token-processing-1.0-SNAPSHOT-jar-with-dependencies.jar")
        verify_as_json(actual)
