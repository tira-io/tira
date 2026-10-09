from django.test import TestCase
from utils_for_testing import dataset_1, set_up_tira_environment

import tira_app.model as modeldb
from tira_app.data.HybridDatabase import HybridDatabase

PARTICIPANT = "example_participant"


class TestRunAsDictSoftwareDeleted(TestCase):
    """Tests for the 'software_deleted' field exposed by HybridDatabase._run_as_dict: whether the
    software/docker-software/upload (i.e., the code submission) that produced a run has been deleted. This
    is independent of the run's own 'deleted' flag, and is used (e.g. by tira-cli admin re-run-evaluations)
    to exclude runs of deleted code submissions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()

    def _dataset(self):
        return modeldb.Dataset.objects.get(dataset_id=dataset_1)

    def _vm(self):
        return modeldb.VirtualMachine.objects.get(vm_id=PARTICIPANT)

    def _task(self):
        return modeldb.Task.objects.get(task_id="shared-task-1")

    def test_software_deleted_is_false_for_non_deleted_software(self):
        software = modeldb.Software.objects.create(
            software_id="software-not-deleted",
            vm=self._vm(),
            task=self._task(),
            count="1",
            creation_date="now",
            last_edit_date="now",
            deleted=False,
        )
        run = modeldb.Run.objects.create(run_id="run-for-software-not-deleted", software=software)

        self.assertFalse(HybridDatabase._run_as_dict(run)["software_deleted"])

    def test_software_deleted_is_true_for_deleted_software(self):
        software = modeldb.Software.objects.create(
            software_id="software-deleted",
            vm=self._vm(),
            task=self._task(),
            count="1",
            creation_date="now",
            last_edit_date="now",
            deleted=True,
        )
        run = modeldb.Run.objects.create(run_id="run-for-deleted-software", software=software)

        self.assertTrue(HybridDatabase._run_as_dict(run)["software_deleted"])

    def test_software_deleted_is_true_for_deleted_docker_software(self):
        docker_software = modeldb.DockerSoftware.objects.create(
            display_name="docker-software-deleted",
            vm=self._vm(),
            task=self._task(),
            deleted=True,
        )
        run = modeldb.Run.objects.create(run_id="run-for-deleted-docker-software", docker_software=docker_software)

        self.assertTrue(HybridDatabase._run_as_dict(run)["software_deleted"])

    def test_software_deleted_is_true_for_deleted_upload(self):
        upload = modeldb.Upload.objects.create(
            vm=self._vm(),
            task=self._task(),
            last_edit_date="now",
            deleted=True,
        )
        run = modeldb.Run.objects.create(run_id="run-for-deleted-upload", upload=upload)

        self.assertTrue(HybridDatabase._run_as_dict(run)["software_deleted"])

    def test_software_deleted_is_false_for_evaluation_runs(self):
        evaluator = modeldb.Evaluator.objects.get(evaluator_id="big-evaluator-for-everything")
        submission = modeldb.Run.objects.create(
            run_id="submission-for-eval-software-deleted-test", input_dataset=self._dataset()
        )
        eval_run = modeldb.Run.objects.create(
            run_id="ts-evaluates-submission-for-eval-software-deleted-test",
            input_run=submission,
            input_dataset=self._dataset(),
            evaluator=evaluator,
        )

        self.assertFalse(HybridDatabase._run_as_dict(eval_run)["software_deleted"])
