import os
import unittest
from pathlib import Path

from tira.profiling_integration import ProfilingIntegration
from tira.rest_api_client import Client


def mocked_tira_client(run_dir):
    class MockedTiraClient:
        def get_run_output(self, approach, dataset, allow_without_evaluation=False):
            return f"{Path(os.path.abspath(__file__)).parent}/{run_dir}"

    return MockedTiraClient()


class ParsingOfProfilingTest(unittest.TestCase):
    def test_error_message_is_thrown_if_no_tira_client_is_available(self):
        tira_client = None
        profiling_integration = ProfilingIntegration(tira_client)
        with self.assertRaises(Exception) as context:
            profiling_integration.from_submission("run_id", "dataset")
        print(context.exception)
        self.assertTrue("No profiling data available for approach" in str(context.exception))

    def test_error_message_is_thrown_if_profile_data_is_available(self):
        tira_client = mocked_tira_client(".")
        profiling_integration = ProfilingIntegration(tira_client)
        with self.assertRaises(Exception) as context:
            profiling_integration.from_submission("run_id", "dataset")
        print(context.exception)
        self.assertTrue("No profiling data available for run" in str(context.exception))

    def test_profiling_info_available_as_dict(self):
        tira_client = mocked_tira_client("/resources/profiling_logs/a")
        profiling_integration = ProfilingIntegration(tira_client)
        expected = {"timestamp": 0.0, "key": "ps_cpu", "value": 0.2}
        actual = profiling_integration.from_submission("run_id", "dataset")

        self.assertEqual(expected, actual[0])

    def test_profiling_info_has_elpsed_time_as_last_slot(self):
        tira_client = mocked_tira_client("/resources/profiling_logs/b")
        profiling_integration = ProfilingIntegration(tira_client)
        expected = {"timestamp": 2.0, "key": "elapsed_time", "value": 2}
        actual = profiling_integration.from_submission("run_id", "dataset")

        self.assertEqual(expected, actual[-1])

    def test_profiling_info_available_as_pd(self):
        tira_client = mocked_tira_client("/resources/profiling_logs/c")
        profiling_integration = ProfilingIntegration(tira_client)
        expected = {"timestamp": 0.0, "key": "ps_cpu", "value": 0.2}
        actual = profiling_integration.from_submission("run_id", "dataset", return_pd=True)

        self.assertEqual(expected, actual.iloc[0].to_dict())

    def test_profiling_info_has_elpsed_time_as_last_slot_from_zip(self):
        tira_client = mocked_tira_client("/resources/profiling_logs2/d")
        profiling_integration = ProfilingIntegration(tira_client)
        expected = {"timestamp": 64.0, "key": "elapsed_time", "value": 64}
        actual = profiling_integration.from_submission("run_id", "dataset")

        self.assertEqual(expected, actual[-1])

    def test_prod_system(self):
        expected = {"timestamp": 38.0, "key": "elapsed_time", "value": 38}
        actual = Client().profiling.from_submission(
            "reneuir-2024/tinyfsu/tiny-fsu-bert", "dl-top-1000-docs-20240701-training"
        )

        self.assertEqual(expected, actual[-1])
