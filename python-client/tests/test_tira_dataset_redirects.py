import unittest

from tira.tira_redirects import redirects, mirror_url
import requests
from hashlib import md5


def md5_of_first_kilobyte_of_http_resource(url):
    if not url.startswith('https://files.webis.de') and not url.startswith('https://zenodo.org/records'):
        raise ValueError(f'URL {url} is not from webis.de respectively zenodo')
    return md5(requests.get(url, headers={'Range': f'bytes=0-1024'}).content).hexdigest()

class TestRedirects(unittest.TestCase):
    def test_redirect_ir_lab_leipzig_wise23_train_inputs(self):
        expected_redirect = 'https://zenodo.org/records/10628882/files/training-20231104-inputs.zip?download=1'
        dataset_url = 'https://www.tira.io/data-download/training/input-/training-20231104-training.zip'

        expected_md5_first_kilobyte = '6e2e445a72e282c25c545154b427d3fd'

        actual_redirect =  redirects(url=dataset_url)['urls'][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)


        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_wise23_train_truths(self):
        expected_redirect = 'https://zenodo.org/records/10628882/files/training-20231104-truths.zip?download=1'
        dataset_url = 'https://www.tira.io/data-download/training/input-truth/training-20231104-training.zip'
        expected_md5_first_kilobyte = '85e40610278e0f37edc519ba6269773d'

        actual_redirect =  redirects(url=dataset_url)['urls'][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_padua_sose23_train_inputs(self):
        expected_redirect = 'https://zenodo.org/records/10628882/files/training-20231104-inputs.zip?download=1'
        dataset_url = 'https://www.tira.io/data-download/training/input-/longeval-tiny-train-20240315-training.zip'

        expected_md5_first_kilobyte = '6e2e445a72e282c25c545154b427d3fd'

        actual_redirect =  redirects(url=dataset_url)['urls'][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)


        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_padua_sose23_train_truths(self):
        expected_redirect = 'https://zenodo.org/records/10628882/files/training-20231104-truths.zip?download=1'
        dataset_url = 'https://www.tira.io/data-download/training/input-truth/longeval-tiny-train-20240315-training.zip'
        expected_md5_first_kilobyte = '85e40610278e0f37edc519ba6269773d'

        actual_redirect =  redirects(url=dataset_url)['urls'][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_wise23_jena_inputs(self):
        expected_redirect = 'https://zenodo.org/records/10628882/files/jena-topics-small-20240119-inputs.zip?download=1'
        dataset_url = 'https://www.tira.io/data-download/training/input-/jena-topics-small-20240119-training.zip'

        expected_md5_first_kilobyte = 'b013dcb175648f0190fb5b5ab9f8cc5b'

        actual_redirect =  redirects(url=dataset_url)['urls'][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)


        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_wise23_jena_truths(self):
        expected_redirect = 'https://zenodo.org/records/10628882/files/jena-topics-small-20240119-truths.zip?download=1'
        dataset_url = 'https://www.tira.io/data-download/training/input-truth/jena-topics-small-20240119-training.zip'
        expected_md5_first_kilobyte = 'b7b4c8ad3e85c418cb144f0dcaf568b2'

        actual_redirect =  redirects(url=dataset_url)['urls'][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_wise23_validation_inputs(self):
        expected_redirect = 'https://zenodo.org/records/10628882/files/validation-20231104-inputs.zip?download=1'
        expected_md5_first_kilobyte = '1ad750ebde6828971ec63cda1d415be6'
        dataset_url = 'https://www.tira.io/data-download/training/input-/validation-20231104-training.zip'

        actual_redirect =  redirects(url=dataset_url)['urls'][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_wise23_leipzig_inputs(self):
        expected_redirect = 'https://zenodo.org/records/10628882/files/leipzig-topics-small-20240119-inputs.zip?download=1'
        dataset_url = 'https://www.tira.io/data-download/training/input-/leipzig-topics-small-20240119-training.zip'

        expected_md5_first_kilobyte = '09a02fdfb03c9797842ff7adc453f850'

        actual_redirect =  redirects(url=dataset_url)['urls'][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)


        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_wise23_leipzig_truths(self):
        expected_redirect = 'https://zenodo.org/records/10628882/files/leipzig-topics-small-20240119-truths.zip?download=1'
        dataset_url = 'https://www.tira.io/data-download/training/input-truth/leipzig-topics-small-20240119-training.zip'
        expected_md5_first_kilobyte = '3420611e46a5381317b9cbacb6a6c164'

        actual_redirect =  redirects(url=dataset_url)['urls'][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_wise23_validation_truths(self):
        expected_redirect = 'https://zenodo.org/records/10628882/files/validation-20231104-truths.zip?download=1'
        expected_md5_first_kilobyte = '7fc0c9fa3b7d3ea7e846d51bbb192928'
        dataset_url = 'https://www.tira.io/data-download/training/input-truth/validation-20231104-training.zip'

        actual_redirect =  redirects(url=dataset_url)['urls'][0]
        self.assertEqual(expected_redirect, actual_redirect)
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)


        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_sose23_inputs(self):
        expected_redirect = 'https://zenodo.org/records/10628640/files/iranthology-20230618-training-inputs.zip?download=1'
        expected_md5_first_kilobyte = 'f0727e93741e50b32270883e821075d0'
        dataset_url = 'https://www.tira.io/data-download/training/input-/iranthology-20230618-training.zip'

        actual_redirect =  redirects(url=dataset_url)['urls'][0]
        self.assertEqual(expected_redirect, actual_redirect)
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_sose23_truths(self):
        expected_redirect = 'https://zenodo.org/records/10628640/files/iranthology-20230618-training-truths.zip?download=1'
        expected_md5_first_kilobyte = '7dd9d2cb48c3bc8515fd0d5c973c5fd8'
        dataset_url = 'https://www.tira.io/data-download/training/input-truth/iranthology-20230618-training.zip'
        

        actual_redirect =  redirects(url=dataset_url)['urls'][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

