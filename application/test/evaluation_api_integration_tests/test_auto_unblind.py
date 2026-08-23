from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from settings_test import TIRA_ROOT
from utils_for_testing import set_up_tira_filesystem

import tira_app.model as modeldb
from tira_app.tira_model import model as tira_model


def _write_run_prototext(dataset_id: str, vm_id: str, run_id: str, software_id: str = "upload") -> None:
    run_dir = TIRA_ROOT / "data" / "runs" / dataset_id / vm_id / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run.prototext").write_text(
        f'\nsoftwareId: "{software_id}"\nrunId: "{run_id}"\ninputDataset: "{dataset_id}"\ndownloadable:'
        " true\ndeleted: false\n"
    )


class TestAutoUnblind(TestCase):
    """Tests that new runs/evaluations are automatically unblinded if the corresponding dataset flag
    (auto_unblind_runs/auto_unblind_evaluation) is set."""

    @classmethod
    def setUpClass(cls):
        set_up_tira_filesystem()
        tira_model.edit_organizer("auto-unblind-organizer", "organizer", "years", "web", [])
        tira_model.add_vm(
            "master-vm-for-auto-unblind-task", "user_name", "initial_user_password", "ip", "host", "12", "12"
        )
        tira_model.create_task(
            "auto-unblind-task",
            "task_name",
            "task_description",
            False,
            "master-vm-for-auto-unblind-task",
            "auto-unblind-organizer",
            "website",
            False,
            False,
            False,
            "help_command",
            "",
            "",
        )
        cls.evaluator = modeldb.Evaluator.objects.update_or_create(evaluator_id="auto-unblind-task-evaluator")[0]

        tira_model.add_dataset(
            "auto-unblind-task", "dataset-with-auto-unblind", "test", "dataset-with-auto-unblind", "upload-name"
        )
        cls.dataset_with_auto_unblind = modeldb.Dataset.objects.get(
            dataset_id__startswith="dataset-with-auto-unblind"
        )
        cls.dataset_with_auto_unblind.auto_unblind_runs = True
        cls.dataset_with_auto_unblind.auto_unblind_evaluation = True
        cls.dataset_with_auto_unblind.evaluator = cls.evaluator
        cls.dataset_with_auto_unblind.save()

        tira_model.add_dataset(
            "auto-unblind-task", "dataset-without-auto-unblind", "test", "dataset-without-auto-unblind", "upload-name"
        )
        cls.dataset_without_auto_unblind = modeldb.Dataset.objects.get(
            dataset_id__startswith="dataset-without-auto-unblind"
        )
        cls.dataset_without_auto_unblind.evaluator = cls.evaluator
        cls.dataset_without_auto_unblind.save()

        tira_model.add_vm("auto-unblind-vm", "user_name", "initial_user_password", "ip", "host", "12", "12")

    def test_new_dataset_defaults_to_auto_unblind_disabled(self):
        self.assertFalse(self.dataset_without_auto_unblind.auto_unblind_runs)
        self.assertFalse(self.dataset_without_auto_unblind.auto_unblind_evaluation)

    def test_run_is_auto_unblinded_if_dataset_has_auto_unblind_runs(self):
        dataset_id = self.dataset_with_auto_unblind.dataset_id
        _write_run_prototext(dataset_id, "auto-unblind-vm", "run-with-auto-unblind")

        tira_model.add_run(dataset_id=dataset_id, vm_id="auto-unblind-vm", run_id="run-with-auto-unblind")

        run = modeldb.Run.objects.get(run_id="run-with-auto-unblind")
        review = modeldb.Review.objects.get(run=run)
        self.assertFalse(review.blinded)

    def test_run_is_not_auto_unblinded_if_dataset_has_no_auto_unblind_runs(self):
        dataset_id = self.dataset_without_auto_unblind.dataset_id
        _write_run_prototext(dataset_id, "auto-unblind-vm", "run-without-auto-unblind")

        tira_model.add_run(dataset_id=dataset_id, vm_id="auto-unblind-vm", run_id="run-without-auto-unblind")

        run = modeldb.Run.objects.get(run_id="run-without-auto-unblind")
        review = modeldb.Review.objects.get(run=run)
        self.assertTrue(review.blinded)

    def test_evaluation_is_auto_unblinded_if_dataset_has_auto_unblind_evaluation(self):
        dataset_id = self.dataset_with_auto_unblind.dataset_id
        _write_run_prototext(dataset_id, "auto-unblind-vm", "run-to-be-evaluated-1")
        tira_model.add_run(dataset_id=dataset_id, vm_id="auto-unblind-vm", run_id="run-to-be-evaluated-1")

        eval_run_dir = TIRA_ROOT / "data" / "runs" / dataset_id / "auto-unblind-vm" / "eval-of-run-to-be-evaluated-1"
        (eval_run_dir / "output").mkdir(parents=True, exist_ok=True)
        (eval_run_dir / "run.prototext").write_text(
            f'\nsoftwareId: "{self.evaluator.evaluator_id}"\nrunId: "eval-of-run-to-be-evaluated-1"\ninputDataset:'
            f' "{dataset_id}"\ninputRun: "run-to-be-evaluated-1"\ndownloadable: true\ndeleted: false\n'
        )

        tira_model.add_run(dataset_id=dataset_id, vm_id="auto-unblind-vm", run_id="eval-of-run-to-be-evaluated-1")

        eval_run = modeldb.Run.objects.get(run_id="eval-of-run-to-be-evaluated-1")
        review = modeldb.Review.objects.get(run=eval_run)
        self.assertFalse(review.blinded)

    def test_evaluation_is_not_auto_unblinded_if_dataset_has_no_auto_unblind_evaluation(self):
        dataset_id = self.dataset_without_auto_unblind.dataset_id
        _write_run_prototext(dataset_id, "auto-unblind-vm", "run-to-be-evaluated-2")
        tira_model.add_run(dataset_id=dataset_id, vm_id="auto-unblind-vm", run_id="run-to-be-evaluated-2")

        eval_run_dir = TIRA_ROOT / "data" / "runs" / dataset_id / "auto-unblind-vm" / "eval-of-run-to-be-evaluated-2"
        (eval_run_dir / "output").mkdir(parents=True, exist_ok=True)
        (eval_run_dir / "run.prototext").write_text(
            f'\nsoftwareId: "{self.evaluator.evaluator_id}"\nrunId: "eval-of-run-to-be-evaluated-2"\ninputDataset:'
            f' "{dataset_id}"\ninputRun: "run-to-be-evaluated-2"\ndownloadable: true\ndeleted: false\n'
        )

        tira_model.add_run(dataset_id=dataset_id, vm_id="auto-unblind-vm", run_id="eval-of-run-to-be-evaluated-2")

        eval_run = modeldb.Run.objects.get(run_id="eval-of-run-to-be-evaluated-2")
        review = modeldb.Review.objects.get(run=eval_run)
        self.assertTrue(review.blinded)

    def test_uploaded_run_is_auto_unblinded_if_dataset_has_auto_unblind_runs(self):
        dataset_id = self.dataset_with_auto_unblind.dataset_id
        upload = tira_model.add_upload("auto-unblind-task", "auto-unblind-vm")

        result = tira_model.add_uploaded_run(
            "auto-unblind-task",
            "auto-unblind-vm",
            dataset_id,
            upload["id"],
            SimpleUploadedFile("run.txt", b"some output", content_type="text/plain"),
        )

        review = modeldb.Review.objects.get(run__run_id=result["run"]["run_id"])
        self.assertFalse(review.blinded)

    def test_uploaded_run_is_not_auto_unblinded_if_dataset_has_no_auto_unblind_runs(self):
        dataset_id = self.dataset_without_auto_unblind.dataset_id
        upload = tira_model.add_upload("auto-unblind-task", "auto-unblind-vm")

        result = tira_model.add_uploaded_run(
            "auto-unblind-task",
            "auto-unblind-vm",
            dataset_id,
            upload["id"],
            SimpleUploadedFile("run.txt", b"some output", content_type="text/plain"),
        )

        review = modeldb.Review.objects.get(run__run_id=result["run"]["run_id"])
        self.assertTrue(review.blinded)

    @classmethod
    def tearDownClass(cls):
        pass
