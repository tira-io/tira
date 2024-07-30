import unittest

from tira.local_execution_integration import LocalExecutionIntegration as Client


class TestLocalExecutionIntegrationTest(unittest.TestCase):
    def test_01(self):
        expected = "registry.webis.de/code-research/tira/tira-user-dam/seupd2324:latest"
        actual = Client().normalize_image_name("seupd2324", "registry.webis.de/code-research/tira/tira-user-dam/")

        self.assertEqual(expected, actual)

    def test_02(self):
        expected = "registry.webis.de/code-research/tira/tira-user-dam/seupd2324:latest"
        actual = Client().normalize_image_name(
            "seupd2324-dam-baseline", "registry.webis.de/code-research/tira/tira-user-dam/"
        )

        self.assertEqual(expected, actual)

    def test_03(self):
        expected = "registry.webis.de/code-research/tira/tira-user-petropoulossiblings/panospetr:1.1.2"
        actual = Client().normalize_image_name(
            "panospetr/av-software-petropoulos-pan2024:1.1.2",
            "registry.webis.de/code-research/tira/tira-user-petropoulossiblings/",
        )

        self.assertEqual(expected, actual)

    def test_04(self):
        expected = "registry.webis.de/code-research/tira/tira-user-petropoulossiblings/bash:latest"
        actual = Client().normalize_image_name(
            "bash:latest", "registry.webis.de/code-research/tira/tira-user-petropoulossiblings/"
        )

        self.assertEqual(expected, actual)
