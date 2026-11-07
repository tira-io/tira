from datetime import datetime

from django.test import TestCase
from utils_for_testing import dataset_1, set_up_tira_environment

import tira_app.model as modeldb
from tira_app.endpoints.v1._admin import aggregate_run_statistics

TASK = "shared-task-1"


class TestRunStatistics(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()
        vm = modeldb.VirtualMachine.objects.get(vm_id="PARTICIPANT-FOR-TEST-1")
        task = modeldb.Task.objects.get(task_id=TASK)
        dataset = modeldb.Dataset.objects.get(dataset_id=dataset_1)
        software = modeldb.DockerSoftware.objects.create(display_name="s", vm=vm, task=task)
        upload = modeldb.Upload.objects.create(vm=vm, task=task, dataset=dataset)

        def run(run_id, **kwargs):
            return modeldb.Run.objects.create(run_id=run_id, task=task, input_dataset=dataset, **kwargs)

        run("2031-01-01-10-00-00-a", docker_software=software)
        reviewed = run("2031-01-01-11-00-00-b", docker_software=software)
        modeldb.Review.objects.create(run=reviewed, has_no_errors=True)
        run("2031-01-01-12-00-00-c", upload=upload)
        # A review row without a verdict (as created together with runs) is still unreviewed.
        pending = run("2031-01-01-13-00-00-e", docker_software=software, input_run=reviewed)
        modeldb.Review.objects.create(run=pending)
        run("2031-01-01-14-00-00-f", evaluator=modeldb.Evaluator.objects.first(), input_run=reviewed)
        run("2032-01-01-12-00-00-d", upload=upload)

    def test_counts_runs_within_time_range(self):
        stats = aggregate_run_statistics(datetime(2031, 1, 1), datetime(2031, 12, 31))

        self.assertEqual(
            [{"task": TASK, "executed_code_submissions": 3, "run_uploads": 1, "unreviewed": 3}], stats
        )

    def test_empty_for_range_without_runs(self):
        self.assertEqual([], aggregate_run_statistics(datetime(2040, 1, 1), datetime(2040, 12, 31)))
