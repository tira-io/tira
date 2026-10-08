import json
import os
import zipfile
from io import BytesIO
from unittest.mock import patch

import yaml
from django.http.request import QueryDict
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from utils_for_testing import method_for_url_pattern, set_up_tira_environment

import tira_app.model as modeldb
import tira_app.tira_model as tira_model
from tira_app.endpoints.task_exports import (
    ExportError,
    _is_included_in_trec_auto_judge,
    _priority_of_submission,
    _run_output_files,
    _trec_auto_judge_export,
    task_export,
)

task_function = method_for_url_pattern("api/task/<str:task_id>")
ADMIN = "admins"
PARTICIPANT = "tira_vm_PARTICIPANT-FOR-TEST-1"


def _request(groups, method="get"):
    factory = APIRequestFactory()
    request = getattr(factory, method)(
        "/ignored",
        HTTP_X_DISRAPTOR_APP_SECRET_KEY=os.getenv("DISRAPTOR_APP_SECRET_KEY"),
        HTTP_X_DISRAPTOR_USER="ignored-user.",
        HTTP_X_DISRAPTOR_GROUPS=groups,
        CSRF_COOKIE="aasa",
    )
    request.GET = QueryDict("", mutable=True)
    return request


class TestNormalizeExportButtons(TestCase):
    def test_normalize_export_buttons_accepts_valid_configuration(self):
        buttons = [{"display_name": "Example Export", "value": "example-zip-export"}]

        self.assertEqual(buttons, modeldb.normalize_export_buttons(buttons))

    def test_normalize_export_buttons_accepts_json_string(self):
        buttons = [{"display_name": "Example Export", "value": "example-zip-export"}]

        self.assertEqual(buttons, modeldb.normalize_export_buttons(json.dumps(buttons)))

    def test_normalize_export_buttons_rejects_unknown_value(self):
        buttons = [{"display_name": "Not Implemented", "value": "does-not-exist"}]

        self.assertIsNone(modeldb.normalize_export_buttons(buttons))

    def test_normalize_export_buttons_rejects_missing_display_name(self):
        buttons = [{"value": "example-zip-export"}]

        self.assertIsNone(modeldb.normalize_export_buttons(buttons))

    def test_normalize_export_buttons_rejects_malformed_entries(self):
        self.assertIsNone(modeldb.normalize_export_buttons(["not-a-dict"]))

    def test_normalize_export_buttons_rejects_non_list(self):
        self.assertIsNone(modeldb.normalize_export_buttons({"display_name": "x", "value": "example-zip-export"}))

    def test_normalize_export_buttons_handles_none_and_empty(self):
        self.assertIsNone(modeldb.normalize_export_buttons(None))
        self.assertIsNone(modeldb.normalize_export_buttons(""))
        self.assertIsNone(modeldb.normalize_export_buttons([]))


class TestTaskExportButtonsPersistence(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()

    def test_edit_task_persists_export_buttons(self):
        tira_model.edit_task(
            "shared-task-1",
            "Shared Task 1",
            "Updated description",
            False,
            "master-vm-for-task-1",
            "organizer",
            "website",
            False,
            False,
            False,
            allowed_task_teams="",
            export_buttons=[{"display_name": "Example Export", "value": "example-zip-export"}],
        )

        task = modeldb.Task.objects.get(task_id="shared-task-1")
        self.assertEqual(
            [{"display_name": "Example Export", "value": "example-zip-export"}],
            task.get_export_buttons(),
        )

    def test_edit_task_drops_invalid_export_buttons(self):
        tira_model.edit_task(
            "shared-task-1",
            "Shared Task 1",
            "Updated description",
            False,
            "master-vm-for-task-1",
            "organizer",
            "website",
            False,
            False,
            False,
            allowed_task_teams="",
            export_buttons=[{"display_name": "Bad", "value": "not-registered"}],
        )

        task = modeldb.Task.objects.get(task_id="shared-task-1")
        self.assertIsNone(task.get_export_buttons())

    def test_task_endpoint_returns_configured_export_buttons(self):
        modeldb.Task.objects.filter(task_id="shared-task-1").update(
            export_buttons=json.dumps([{"display_name": "Example Export", "value": "example-zip-export"}])
        )

        response = task_function(_request(PARTICIPANT), task_id="shared-task-1")

        self.assertEqual(200, response.status_code)
        content = json.loads(response.content)
        self.assertEqual(
            [{"display_name": "Example Export", "value": "example-zip-export"}],
            content["context"]["task"]["export_buttons"],
        )


class TestTaskExportEndpoint(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()

    def setUp(self):
        modeldb.Task.objects.filter(task_id="shared-task-1").update(
            export_buttons=json.dumps([{"display_name": "Example Export", "value": "example-zip-export"}])
        )

    def test_admin_can_download_configured_export(self):
        response = task_export(
            _request(ADMIN), task_id="shared-task-1", vm_id="master-vm-for-task-1", value="example-zip-export"
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/zip", response["Content-Type"])
        zipf = zipfile.ZipFile(BytesIO(response.content))
        self.assertEqual(["export.txt"], zipf.namelist())
        self.assertIn("shared-task-1", zipf.read("export.txt").decode())

    def test_admin_gets_404_for_unconfigured_value(self):
        response = task_export(
            _request(ADMIN), task_id="shared-task-1", vm_id="master-vm-for-task-1", value="not-configured-value"
        )

        self.assertEqual(404, response.status_code)

    def test_non_admin_participant_of_other_vm_is_denied(self):
        response = task_export(
            _request(PARTICIPANT),
            task_id="shared-task-1",
            vm_id="master-vm-for-task-1",
            value="example-zip-export",
        )

        self.assertNotEqual(200, response.status_code)

    def test_guest_is_redirected_to_login(self):
        response = task_export(
            _request(""), task_id="shared-task-1", vm_id="master-vm-for-task-1", value="example-zip-export"
        )

        self.assertEqual(302, response.status_code)


class TestPriorityOfSubmission(TestCase):
    def test_parses_valid_integer_priority(self):
        self.assertEqual(5, _priority_of_submission({"priority": "5"}))

    def test_parses_priority_with_different_case_key(self):
        self.assertEqual(7, _priority_of_submission({"Priority": "7"}))

    def test_parses_priority_with_surrounding_whitespace(self):
        self.assertEqual(3, _priority_of_submission({"priority": "  3  "}))

    def test_returns_none_for_missing_metadata(self):
        self.assertIsNone(_priority_of_submission(None))
        self.assertIsNone(_priority_of_submission({}))

    def test_returns_none_for_missing_priority_key(self):
        self.assertIsNone(_priority_of_submission({"description": "a run"}))

    def test_returns_none_for_non_numeric_priority(self):
        self.assertIsNone(_priority_of_submission({"priority": "not-a-number"}))


class TestIsIncludedInTrecAutoJudge(TestCase):
    def test_includes_priorities_between_one_and_ten_inclusive(self):
        for priority in range(1, 11):
            self.assertTrue(_is_included_in_trec_auto_judge({"priority": str(priority)}))

    def test_excludes_priority_zero_or_below(self):
        self.assertFalse(_is_included_in_trec_auto_judge({"priority": "0"}))
        self.assertFalse(_is_included_in_trec_auto_judge({"priority": "-1"}))

    def test_excludes_priority_above_ten(self):
        self.assertFalse(_is_included_in_trec_auto_judge({"priority": "11"}))

    def test_excludes_missing_or_unparseable_priority(self):
        self.assertFalse(_is_included_in_trec_auto_judge(None))
        self.assertFalse(_is_included_in_trec_auto_judge({}))
        self.assertFalse(_is_included_in_trec_auto_judge({"priority": "abc"}))


class TestRunOutputFiles(TestCase):
    def test_returns_sorted_files_of_an_existing_run_output_dir(self):
        from django.conf import settings

        run_output_dir = settings.TIRA_ROOT / "data" / "runs" / "some-dataset" / "some-vm" / "some-run" / "output"
        run_output_dir.mkdir(parents=True, exist_ok=True)
        (run_output_dir / "b.txt").write_text("b")
        (run_output_dir / "a.txt").write_text("a")
        (run_output_dir / "subdir").mkdir(exist_ok=True)
        (run_output_dir / "subdir" / "c.txt").write_text("c")

        files = _run_output_files("some-dataset", "some-vm", "some-run")

        self.assertEqual(
            ["a.txt", "b.txt", "subdir/c.txt"],
            [str(f.relative_to(run_output_dir)) for f in files],
        )

    def test_returns_empty_list_for_non_existing_run(self):
        self.assertEqual([], _run_output_files("no-such-dataset", "no-such-vm", "no-such-run"))


class TestTrecAutoJudgeExport(TestCase):
    """Uses mocks for the data layer (model.get_docker_softwares_with_runs) and for the per-run file lookup
    instead of building full database/filesystem fixtures, since _trec_auto_judge_export only orchestrates
    those two seams."""

    def _software(self, docker_software_id, display_name, metadata, runs):
        return {
            "docker_software_id": docker_software_id,
            "display_name": display_name,
            "metadata": metadata,
            "runs": runs,
        }

    def _run(self, run_id, dataset, is_evaluation=False):
        return {"run_id": run_id, "dataset": dataset, "is_evaluation": is_evaluation}

    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_excludes_software_without_qualifying_priority(self, get_docker_softwares_with_runs, add_run_to_zip):
        get_docker_softwares_with_runs.return_value = [
            self._software(1, "No Metadata", None, [self._run("run-1", "rag26-20260827_1-test")]),
            self._software(2, "Priority Too High", {"priority": "11"}, [self._run("run-2", "rag26-20260827_1-test")]),
            self._software(3, "Priority Zero", {"priority": "0"}, [self._run("run-3", "rag26-20260827_1-test")]),
        ]

        with self.assertRaises(ExportError):
            _trec_auto_judge_export("auto-judge-task", {"task_name": "AutoJudge"}, "some-vm")

        add_run_to_zip.assert_not_called()

    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_includes_qualifying_software_with_zip_and_yaml(self, get_docker_softwares_with_runs, add_run_to_zip):
        get_docker_softwares_with_runs.return_value = [
            self._software(
                1,
                "Xy hello",
                {"priority": "5"},
                [
                    self._run("run-id-01", "rag26-20260827_1-test"),
                    self._run("run-id-02", "ragtime26-20260827-test"),
                    self._run("run-id-eval", "rag26-20260827_1-test", is_evaluation=True),
                    self._run("run-id-other-dataset", "some-other-dataset"),
                ],
            )
        ]

        response = _trec_auto_judge_export("auto-judge-task", {"task_name": "AutoJudge"}, "some-vm")

        self.assertEqual("application/zip", response["Content-Type"])
        self.assertIn("auto-judge-task-trec-auto-judge-export.zip", response["Content-Disposition"])

        zipf = zipfile.ZipFile(BytesIO(response.content))
        self.assertEqual({"Xy hello.zip", "Xy hello.yaml"}, set(zipf.namelist()))

        metadata = yaml.safe_load(zipf.read("Xy hello.yaml").decode())
        self.assertIn("zip_size_bytes", metadata)
        self.assertIn("zip_md5sum", metadata)
        self.assertEqual("Xy hello", metadata["submission"]["display_name"])

        # Only the two non-evaluation runs on the configured auto-judge datasets are added to the per-software
        # zip; the evaluation run and the run on an unrelated dataset are skipped.
        calls = [call.args for call in add_run_to_zip.call_args_list]
        self.assertEqual(2, len(calls))
        self.assertEqual(("rag26-20260827_1-test", "some-vm", "run-id-01", "rag26"), calls[0][1:])
        self.assertEqual(("ragtime26-20260827-test", "some-vm", "run-id-02", "ragtime26"), calls[1][1:])

    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_handles_no_qualifying_software(self, get_docker_softwares_with_runs):
        get_docker_softwares_with_runs.return_value = []

        with self.assertRaises(ExportError):
            _trec_auto_judge_export("auto-judge-task", {"task_name": "AutoJudge"}, "some-vm")


class TestTrecAutoJudgeExportEndpoint(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()

    def setUp(self):
        modeldb.Task.objects.filter(task_id="shared-task-1").update(
            export_buttons=json.dumps([{"display_name": "AutoJudge Export", "value": "trec-auto-judge"}])
        )

    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_admin_gets_400_with_message_when_export_would_be_empty(self, get_docker_softwares_with_runs):
        get_docker_softwares_with_runs.return_value = []

        response = task_export(
            _request(ADMIN), task_id="shared-task-1", vm_id="master-vm-for-task-1", value="trec-auto-judge"
        )

        self.assertEqual(400, response.status_code)
        content = json.loads(response.content)
        self.assertIn("would be empty", content["message"])
        get_docker_softwares_with_runs.assert_called_once_with(
            "shared-task-1", "master-vm-for-task-1", return_code_submissions=True
        )

    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_admin_can_download_trec_auto_judge_export_with_qualifying_submission(self, get_docker_softwares_with_runs):
        get_docker_softwares_with_runs.return_value = [
            {
                "docker_software_id": 1,
                "display_name": "Xy hello",
                "metadata": {"priority": "5"},
                "runs": [],
            }
        ]

        response = task_export(
            _request(ADMIN), task_id="shared-task-1", vm_id="master-vm-for-task-1", value="trec-auto-judge"
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/zip", response["Content-Type"])
        zipf = zipfile.ZipFile(BytesIO(response.content))
        self.assertEqual({"Xy hello.zip", "Xy hello.yaml"}, set(zipf.namelist()))
