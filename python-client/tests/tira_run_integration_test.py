#from approvaltests import verify_as_json
import unittest
from subprocess import check_output
from tira.tira_run import main
import sys
import tempfile
import os

def foo(image):
    orig_argv = list(sys.argv)
    temp_dir = '/tmp/' + tempfile.TemporaryDirectory().name
    os.makedirs(temp_dir, exist_ok=True)

    sys.argv = ['tira-run', '--input-dataset', 'workshop-on-open-web-search/document-processing-20231027-training', '--image', image, '--output-dir', 'fffff']
    main()
    sys.argv = orig_argv


class TiraRunIntegrationTest(unittest.TestCase):

    def testfoo(self):
        image = 'dockerfile_multi_stage_bash'
        check_output(['docker', 'build', '-t', image, '-f', f'tests/resources/{image}', '.'])
        
        #foo(image)
        #raise ValueError('sda')
