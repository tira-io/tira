from _utils.mixins import StrAssertMixins
from api_access_matrix import ADMIN
from django.test import TestCase
from utils_for_testing import method_for_url_pattern, mock_request, set_up_tira_environment

url = "serp/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/<int:topk>/<str:run_id>"
diffir = method_for_url_pattern(url)


class TestDiffirEndpoint(TestCase, StrAssertMixins):
    @classmethod
    def setUpClass(cls):
        set_up_tira_environment()

    def test_diffir_with_json(self):
        # Arrange
        request = mock_request(
            ADMIN,
            url,
            params={
                "task_id": "<str:task_id>",  # "t1",
                "vm_id": "<str:vm_id>",  # "example_participant",
                "dataset_id": "<str:dataset_id>",  # "dataset-1",
                "topk": "<int:topk>",  # 10,
                "run_id": "<str:run_id>",  # "run-3-example_participant",
            },
        )

        # Act
        actual = diffir(
            request,
            vm_id="example_participant",
            dataset_id="dataset-1",
            task_id="t1",
            run_id="run-3-example_participant",
            topk=10,
        )

        # Assert
        self.assertStartsWith(actual.content.decode("utf-8"), "<!doctype html>")

    def test_diffir_with_json_gz(self):
        # Arrange
        request = mock_request(
            ADMIN,
            url,
            params={
                "task_id": "<str:task_id>",  # "t1",
                "vm_id": "<str:vm_id>",  # "example_participant",
                "dataset_id": "<str:dataset_id>",  # "dataset-1",
                "topk": "<int:topk>",  # 10,
                "run_id": "<str:run_id>",  # "run-5-example_participant",
            },
        )

        # Act
        actual = diffir(
            request,
            vm_id="example_participant",
            dataset_id="dataset-1",
            task_id="t1",
            run_id="run-5-example_participant",
            topk=10,
        )

        # Assert
        self.assertStartsWith(actual.content.decode("utf-8"), "<!doctype html>")

    @classmethod
    def tearDownClass(cls):
        pass
