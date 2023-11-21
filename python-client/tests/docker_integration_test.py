from tira.local_execution_integration import LocalExecutionIntegration as Client
import tempfile

def test_export_of_file_from_bash_image():
    tira = Client()
    local_file = tempfile.NamedTemporaryFile().name
    tira.export_file_from_software('/etc/issue', local_file, image='bash:alpine3.16')
    
    actual = open(local_file).read()
    expected = '''Welcome to Alpine Linux 3.16
Kernel \\r on an \\m (\\l)

'''
    assert actual == expected

def test_export_of_file():
    tira = Client()
    local_file = tempfile.NamedTemporaryFile().name
    tira.export_file_from_software('/etc/alpine-release', local_file, image='bash:alpine3.16')
    
    actual = open(local_file).read()
    expected = '''3.16.5\n'''
    assert actual == expected

def test_extraction_of_entrypoint():
    expected = 'docker-entrypoint.sh'

    tira = Client()
    actual = tira.extract_entrypoint(image='bash:alpine3.16')

    assert actual == expected

