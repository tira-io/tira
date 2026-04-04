import unittest
from unittest.mock import patch
from tira.io_utils import dockerfile_for_architecture  

class TestDockerfileForArchitecture(unittest.TestCase):
    @patch('platform.machine')
    @patch('os.path.exists')
    def test_x86_64_returns_dockerfile(self, mock_exists, mock_machine):
        mock_machine.return_value = 'x86_64'
        result = dockerfile_for_architecture()
        self.assertEqual(result, 'Dockerfile')

    @patch('platform.machine')
    def test_arm64_returns_dockerfile_arm64(self, mock_machine):
        mock_machine.return_value = 'arm64'
        with patch('os.path.exists', return_value=True):  
            result = dockerfile_for_architecture()
            self.assertEqual(result, 'Dockerfile.arm64')

    @patch('platform.machine')
    def test_arm64_variant_aarch(self, mock_machine):
        mock_machine.return_value = 'aarch64'
        with patch('os.path.exists', return_value=True):
            result = dockerfile_for_architecture()
            self.assertEqual(result, 'Dockerfile.arm64')

    @patch('platform.machine')
    @patch('os.path.exists', return_value=False)
    def test_arm64_fallback_to_dockerfile(self, mock_exists, mock_machine):
        mock_machine.return_value = 'arm64'
        result = dockerfile_for_architecture()
        self.assertEqual(result, 'Dockerfile')

    @patch('platform.machine')
    @patch('os.path.exists', return_value=False)
    def test_aarch64_fallback_to_dockerfile(self, mock_exists, mock_machine):
        mock_machine.return_value = 'aarch64'
        result = dockerfile_for_architecture()
        self.assertEqual(result, 'Dockerfile')