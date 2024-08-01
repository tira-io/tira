# from approvaltests import verify_as_json
import os
import sys
import tempfile
import unittest

from tests.jupyter_notebook_pipeline_construction_test import build_docker_image
from tira.tira_run import main


def foo(image):
    orig_argv = list(sys.argv)
    temp_dir = "/tmp/" + tempfile.TemporaryDirectory().name
    os.makedirs(temp_dir, exist_ok=True)

    sys.argv = [
        "tira-run",
        "--input-dataset",
        "workshop-on-open-web-search/document-processing-20231027-training",
        "--image",
        image,
        "--output-dir",
        "fffff",
    ]
    main()
    sys.argv = orig_argv


class TiraRunIntegrationTest(unittest.TestCase):

    def testfoo(self):
        build_docker_image("dockerfile_multi_stage_bash")

        # foo(image)
        # raise ValueError('sda')
