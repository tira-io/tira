from tira.local_execution_integration import LocalExecutionIntegration as Client
import unittest

class TestLocalExecutionIntegrationTest(unittest.TestCase):
    def test_01(self):
        expected = 'registry.webis.de/code-research/tira/tira-user-dam/seupd2324:latest'
        actual = Client().normalize_image_name('seupd2324', 'registry.webis.de/code-research/tira/tira-user-dam/')

        self.assertEqual(expected, actual)

    def test_02(self):
        expected = 'registry.webis.de/code-research/tira/tira-user-dam/seupd2324:latest'
        actual = Client().normalize_image_name('seupd2324-dam-baseline', 'registry.webis.de/code-research/tira/tira-user-dam/')

        self.assertEqual(expected, actual)