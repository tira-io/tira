import unittest
from hashlib import md5

import requests

from tira.tira_redirects import mirror_url, redirects


def md5_of_first_kilobyte_of_http_resource(url):
    if not url.startswith("https://files.webis.de") and not url.startswith("https://zenodo.org/records"):
        raise ValueError(f"URL {url} is not from webis.de respectively zenodo")
    return md5(requests.get(url, headers={"Range": "bytes=0-1024"}).content).hexdigest()


class TestRedirects(unittest.TestCase):
    def test_redirect_ir_lab_leipzig_wise23_train_inputs(self):
        expected_redirect = "https://zenodo.org/records/10628882/files/training-20231104-inputs.zip?download=1"
        dataset_url = "https://www.tira.io/data-download/training/input-/training-20231104-training.zip"

        expected_md5_first_kilobyte = "6e2e445a72e282c25c545154b427d3fd"

        actual_redirect = redirects(url=dataset_url)["urls"][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_wise23_train_truths(self):
        expected_redirect = "https://zenodo.org/records/10628882/files/training-20231104-truth.zip?download=1"
        dataset_url = "https://www.tira.io/data-download/training/input-truth/training-20231104-training.zip"
        expected_md5_first_kilobyte = "6d1ef9e09c40e9b0664366a2a003fa64"

        actual_redirect = redirects(url=dataset_url)["urls"][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_padua_sose23_train_inputs(self):
        expected_redirect = "https://zenodo.org/records/10628882/files/training-20231104-inputs.zip?download=1"
        dataset_url = "https://www.tira.io/data-download/training/input-/longeval-tiny-train-20240315-training.zip"

        expected_md5_first_kilobyte = "6e2e445a72e282c25c545154b427d3fd"

        actual_redirect = redirects(url=dataset_url)["urls"][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_padua_sose23_train_truths(self):
        expected_redirect = "https://zenodo.org/records/10628882/files/training-20231104-truth.zip?download=1"
        dataset_url = "https://www.tira.io/data-download/training/input-truth/longeval-tiny-train-20240315-training.zip"
        expected_md5_first_kilobyte = "6d1ef9e09c40e9b0664366a2a003fa64"

        actual_redirect = redirects(url=dataset_url)["urls"][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_wise23_jena_inputs(self):
        expected_redirect = "https://zenodo.org/records/10628882/files/jena-topics-small-20240119-inputs.zip?download=1"
        dataset_url = "https://www.tira.io/data-download/training/input-/jena-topics-small-20240119-training.zip"

        expected_md5_first_kilobyte = "b013dcb175648f0190fb5b5ab9f8cc5b"

        actual_redirect = redirects(url=dataset_url)["urls"][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_wise23_jena_truths(self):
        expected_redirect = "https://zenodo.org/records/10628882/files/jena-topics-small-20240119-truth.zip?download=1"
        dataset_url = "https://www.tira.io/data-download/training/input-truth/jena-topics-small-20240119-training.zip"
        expected_md5_first_kilobyte = "aa25f6931bed856fdb29d0374ff107e3"

        actual_redirect = redirects(url=dataset_url)["urls"][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_wise23_validation_inputs(self):
        expected_redirect = "https://zenodo.org/records/10628882/files/validation-20231104-inputs.zip?download=1"
        expected_md5_first_kilobyte = "1ad750ebde6828971ec63cda1d415be6"
        dataset_url = "https://www.tira.io/data-download/training/input-/validation-20231104-training.zip"

        actual_redirect = redirects(url=dataset_url)["urls"][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_wise23_leipzig_inputs(self):
        expected_redirect = (
            "https://zenodo.org/records/10628882/files/leipzig-topics-small-20240119-inputs.zip?download=1"
        )
        dataset_url = "https://www.tira.io/data-download/training/input-/leipzig-topics-small-20240119-training.zip"

        expected_md5_first_kilobyte = "09a02fdfb03c9797842ff7adc453f850"

        actual_redirect = redirects(url=dataset_url)["urls"][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_wise23_leipzig_truths(self):
        expected_redirect = (
            "https://zenodo.org/records/10628882/files/leipzig-topics-small-20240119-truth.zip?download=1"
        )
        dataset_url = (
            "https://www.tira.io/data-download/training/input-truth/leipzig-topics-small-20240119-training.zip"
        )
        expected_md5_first_kilobyte = "7a60ab76ed8c3423bd407932a1e7e910"

        actual_redirect = redirects(url=dataset_url)["urls"][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_wise23_validation_truths(self):
        expected_redirect = "https://zenodo.org/records/10628882/files/validation-20231104-truth.zip?download=1"
        expected_md5_first_kilobyte = "92ba3a87c1d4cceebccbefd1aa5f944e"
        dataset_url = "https://www.tira.io/data-download/training/input-truth/validation-20231104-training.zip"

        actual_redirect = redirects(url=dataset_url)["urls"][0]
        self.assertEqual(expected_redirect, actual_redirect)
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_sose23_inputs(self):
        expected_redirect = (
            "https://zenodo.org/records/10628640/files/iranthology-20230618-training-inputs.zip?download=1"
        )
        expected_md5_first_kilobyte = "f0727e93741e50b32270883e821075d0"
        dataset_url = "https://www.tira.io/data-download/training/input-/iranthology-20230618-training.zip"

        actual_redirect = redirects(url=dataset_url)["urls"][0]
        self.assertEqual(expected_redirect, actual_redirect)
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)

    def test_redirect_ir_lab_leipzig_sose23_truths(self):
        expected_redirect = (
            "https://zenodo.org/records/10628640/files/iranthology-20230618-training-truths.zip?download=1"
        )
        expected_md5_first_kilobyte = "7dd9d2cb48c3bc8515fd0d5c973c5fd8"
        dataset_url = "https://www.tira.io/data-download/training/input-truth/iranthology-20230618-training.zip"

        actual_redirect = redirects(url=dataset_url)["urls"][0]
        actual_mirror = mirror_url(actual_redirect)
        actual_md5_first_kilobyte = md5_of_first_kilobyte_of_http_resource(actual_redirect)

        self.assertEqual(expected_redirect, actual_redirect)
        self.assertEqual(expected_redirect, actual_mirror)
        self.assertEqual(expected_md5_first_kilobyte, actual_md5_first_kilobyte)
