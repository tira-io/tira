import tempfile
import unittest

from tira.local_execution_integration import LocalExecutionIntegration as Client

# .. todo:: there are no assertions in this file


class TestDockerIntegration(unittest.TestCase):
    def test_export_of_file_from_bash_image(self):
        tira = Client()
        local_file = tempfile.NamedTemporaryFile().name
        tira.export_file_from_software("/etc/issue", local_file, image="bash:alpine3.16")

        actual = open(local_file).read()
        expected = """Welcome to Alpine Linux 3.16
Kernel \\r on an \\m (\\l)

"""
        assert actual == expected

    def test_export_of_file(self):
        tira = Client()
        local_file = tempfile.NamedTemporaryFile().name
        tira.export_file_from_software("/etc/alpine-release", local_file, image="bash:alpine3.16")

        actual = open(local_file).read()
        expected = """3.16.5\n"""
        assert actual == expected

    def test_extraction_of_entrypoint(self):
        expected = "/docker-entrypoint.sh"

        tira = Client()
        actual = tira.extract_entrypoint(image="docker.io/bash:alpine3.16")

        assert actual == expected

    # def test_execution_of_software(self):
    #    tira = Client()
    #    tira.run(image='bash:alpine3.16', command='sleep 2s;', input_dir="/tmp/input", output_dir="/tmp/output")
