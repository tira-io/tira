import io
import unittest
from contextlib import redirect_stdout

from tira.tira_redirects import redirects


def capture_potential_license_agreement(url):
    f = io.StringIO()
    with redirect_stdout(f):
        redirects(url=url)

    return f.getvalue()


class PrintLicenseAgreementTest(unittest.TestCase):
    def test_no_license_agreement_for_unrelated_url(self):
        url = "https://webis.de/"
        expected = ""

        actual = capture_potential_license_agreement(url)
        self.assertEqual(expected, actual)

    def test_no_license_agreement_for_run_download_with_non_license_dataset(self):
        url = (
            "https://www.tira.io/task/ir-benchmarks/user/fschlatt/dataset/antique-test-20230107-training/download/"
            "2024-01-15-15-48-32.zip"
        )
        expected = ""

        actual = capture_potential_license_agreement(url)
        self.assertEqual(expected, actual)

    def test_qwant_license_agreement_for_run_download_01(self):
        expected = (
            'The download is derived from The LongEval Dataset under the "Qwant LongEval'
            ' Attribution-NonCommercial-ShareAlike License". Hence, the download is also under this License. By using'
            " it, you agree to the terms of this license. Please find details at:"
            " https://lindat.mff.cuni.cz/repository/xmlui/page/Qwant_LongEval_BY-NC-SA_License\n"
        )
        datasets = [
            "longeval-train-20230513-training",
            "longeval-short-july-20230513-training",
            "longeval-long-september-20230513-training",
            "longeval-heldout-20230513-training",
            "longeval-2023-08-20240418-training",
            "longeval-2023-06-20240418-training",
            "jena-topics-20231026-test",
            "jena-topics-small-20240119-training",
            "leipzig-topics-20231025-test",
            "leipzig-topics-small-20240119-training",
            "training-20231104-training",
            "validation-20231104-training",
            "longeval-tiny-train-20240315-training",
            "longeval-2023-08-20240423-training",
            "longeval-2023-06-20240423-training",
        ]

        for dataset in datasets:
            url = (
                f"https://www.tira.io/task/ir-benchmarks/user/fschlatt/dataset/{dataset}/download/"
                "2024-01-15-15-48-32.zip"
            )
            actual = capture_potential_license_agreement(url)
            self.assertEqual(expected, actual, dataset)
