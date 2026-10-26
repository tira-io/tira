import json
import os
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import yaml
from django.http.request import QueryDict
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from utils_for_testing import method_for_url_pattern, set_up_tira_environment

import tira_app.model as modeldb
import tira_app.tira_model as tira_model
from tira_app.endpoints.task_exports import (
    TREC_AUTO_JUDGE_EXCLUDED_SUBMISSION_FIELDS,
    ExportError,
    _allow_incomplete_trec_auto_judge_names,
    _evalbase_team_id_for_trec_auto_judge,
    _is_included_in_trec_auto_judge,
    _merge_trec_auto_judge_uploads,
    _priority_of_submission,
    _run_output_files,
    _runs_on_required_datasets,
    _safe_run_id_path_component,
    _sanitized_trec_auto_judge_submission,
    _trec_auto_judge_export,
    _translated_trec_auto_judge_name,
    task_export,
    valid_trec_run_id,
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


class TestValidTrecRunId(TestCase):
    def test_accepts_valid_run_ids(self):
        self.assertTrue(valid_trec_run_id("run-1234"))
        self.assertTrue(valid_trec_run_id("Run_ID-01"))
        self.assertTrue(valid_trec_run_id("abcd"))
        self.assertTrue(valid_trec_run_id("a" * 19))

    def test_rejects_run_ids_that_are_too_short(self):
        self.assertFalse(valid_trec_run_id(""))
        self.assertFalse(valid_trec_run_id("a"))
        self.assertFalse(valid_trec_run_id("abc"))

    def test_rejects_run_ids_that_are_too_long(self):
        self.assertFalse(valid_trec_run_id("a" * 20))
        self.assertFalse(valid_trec_run_id("a" * 21))

    def test_rejects_run_ids_with_disallowed_characters(self):
        self.assertFalse(valid_trec_run_id("run/1234"))
        self.assertFalse(valid_trec_run_id("run 1234"))
        self.assertFalse(valid_trec_run_id("run.1234"))
        self.assertFalse(valid_trec_run_id("../etc/passwd"))
        self.assertFalse(valid_trec_run_id("run#1234"))

    def test_rejects_non_string_or_missing_run_ids(self):
        self.assertFalse(valid_trec_run_id(None))
        self.assertFalse(valid_trec_run_id(1234))
        self.assertFalse(valid_trec_run_id(["run-1234"]))


class TestSafeRunIdPathComponent(TestCase):
    def test_accepts_realistic_timestamp_uuid_run_ids(self):
        # Real TIRA run ids (see tira.io_utils.get_tira_id) are timestamp+uuid based and routinely exceed
        # valid_trec_run_id's length limit, but are perfectly safe path components.
        self.assertTrue(_safe_run_id_path_component("2026-01-01-10-00-00-abcd1234"))
        self.assertTrue(
            _safe_run_id_path_component("2026-01-01-10-00-00-abcd1234-rerank-2026-01-02-11-00-00-efgh5678")
        )

    def test_accepts_short_run_ids(self):
        self.assertTrue(_safe_run_id_path_component("ab"))
        self.assertTrue(_safe_run_id_path_component("a"))

    def test_rejects_run_ids_with_path_separators(self):
        self.assertFalse(_safe_run_id_path_component("run/1234"))
        self.assertFalse(_safe_run_id_path_component("run\\1234"))

    def test_rejects_run_ids_with_dot_dot(self):
        self.assertFalse(_safe_run_id_path_component("../etc/passwd"))
        self.assertFalse(_safe_run_id_path_component("..run1234"))

    def test_rejects_non_string_or_missing_run_ids(self):
        self.assertFalse(_safe_run_id_path_component(None))
        self.assertFalse(_safe_run_id_path_component(""))
        self.assertFalse(_safe_run_id_path_component(1234))
        self.assertFalse(_safe_run_id_path_component(["run-1234"]))


class TestRunsOnRequiredDatasets(TestCase):
    def _run(self, run_id, dataset, is_evaluation=False):
        return {"run_id": run_id, "dataset": dataset, "is_evaluation": is_evaluation}

    def test_groups_runs_by_required_dataset(self):
        runs = [
            self._run("run-1", "rag26-20260827_1-test"),
            self._run("run-2", "ragtime26-20260827-test"),
            self._run("run-3", "rag26-20260827_1-test"),
        ]

        grouped = _runs_on_required_datasets(runs)

        self.assertEqual(["run-1", "run-3"], [r["run_id"] for r in grouped["rag26-20260827_1-test"]])
        self.assertEqual(["run-2"], [r["run_id"] for r in grouped["ragtime26-20260827-test"]])

    def test_excludes_evaluation_runs_and_unrelated_datasets(self):
        runs = [
            self._run("run-eval", "rag26-20260827_1-test", is_evaluation=True),
            self._run("run-other", "some-other-dataset"),
        ]

        grouped = _runs_on_required_datasets(runs)

        self.assertEqual([], grouped["rag26-20260827_1-test"])
        self.assertEqual([], grouped["ragtime26-20260827-test"])

    def test_handles_none_and_empty_runs(self):
        self.assertEqual({"rag26-20260827_1-test": [], "ragtime26-20260827-test": []}, _runs_on_required_datasets(None))
        self.assertEqual({"rag26-20260827_1-test": [], "ragtime26-20260827-test": []}, _runs_on_required_datasets([]))


class TestSanitizedTrecAutoJudgeSubmission(TestCase):
    def test_removes_all_excluded_fields(self):
        software = {field: "ignored-value" for field in TREC_AUTO_JUDGE_EXCLUDED_SUBMISSION_FIELDS}
        software["display_name"] = "Xy hello"
        software["docker_software_id"] = 1
        software["metadata"] = {"priority": "5"}

        sanitized = _sanitized_trec_auto_judge_submission(software)

        self.assertEqual(
            {"display_name": "Xy hello", "docker_software_id": 1, "metadata": {"priority": "5"}}, sanitized
        )
        for field in TREC_AUTO_JUDGE_EXCLUDED_SUBMISSION_FIELDS:
            self.assertNotIn(field, sanitized)

    def test_keeps_fields_not_excluded(self):
        software = {"display_name": "Xy hello", "docker_software_id": 1, "runs": [{"run_id": "r1"}]}

        sanitized = _sanitized_trec_auto_judge_submission(software)

        self.assertEqual({"display_name": "Xy hello", "docker_software_id": 1}, sanitized)


class TestEvalbaseTeamIdForTrecAutoJudge(TestCase):
    def test_returns_evalbase_team_id_for_known_vm(self):
        task = {"task_export_metadata": {"trec-teams": {"some-vm": "team-42"}}}

        self.assertEqual("team-42", _evalbase_team_id_for_trec_auto_judge("auto-judge-task", task, "some-vm"))

    def test_raises_when_task_export_metadata_missing(self):
        with self.assertRaises(ExportError):
            _evalbase_team_id_for_trec_auto_judge("auto-judge-task", {}, "some-vm")

    def test_raises_when_task_export_metadata_is_not_a_dict(self):
        task = {"task_export_metadata": "not-a-dict"}

        with self.assertRaises(ExportError):
            _evalbase_team_id_for_trec_auto_judge("auto-judge-task", task, "some-vm")

    def test_raises_when_trec_teams_field_missing(self):
        task = {"task_export_metadata": {"some-other-field": {}}}

        with self.assertRaises(ExportError):
            _evalbase_team_id_for_trec_auto_judge("auto-judge-task", task, "some-vm")

    def test_raises_when_trec_teams_is_not_a_dict(self):
        task = {"task_export_metadata": {"trec-teams": "not-a-dict"}}

        with self.assertRaises(ExportError):
            _evalbase_team_id_for_trec_auto_judge("auto-judge-task", task, "some-vm")

    def test_raises_when_vm_not_in_trec_teams(self):
        task = {"task_export_metadata": {"trec-teams": {"other-vm": "team-42"}}}

        with self.assertRaises(ExportError):
            _evalbase_team_id_for_trec_auto_judge("auto-judge-task", task, "some-vm")


class TestTranslatedTrecAutoJudgeName(TestCase):
    def test_translates_name_when_entry_exists(self):
        task = {
            "task_export_metadata": {
                "trec-run-id-translation": {"some-vm": {"original-name": "translated-name"}}
            }
        }

        self.assertEqual(
            "translated-name", _translated_trec_auto_judge_name(task, "some-vm", "original-name")
        )

    def test_returns_name_unchanged_when_task_export_metadata_missing(self):
        self.assertEqual("original-name", _translated_trec_auto_judge_name({}, "some-vm", "original-name"))

    def test_returns_name_unchanged_when_task_export_metadata_is_not_a_dict(self):
        task = {"task_export_metadata": "not-a-dict"}

        self.assertEqual("original-name", _translated_trec_auto_judge_name(task, "some-vm", "original-name"))

    def test_returns_name_unchanged_when_translation_table_missing(self):
        task = {"task_export_metadata": {"trec-teams": {"some-vm": "team-42"}}}

        self.assertEqual("original-name", _translated_trec_auto_judge_name(task, "some-vm", "original-name"))

    def test_returns_name_unchanged_when_translation_table_is_not_a_dict(self):
        task = {"task_export_metadata": {"trec-run-id-translation": "not-a-dict"}}

        self.assertEqual("original-name", _translated_trec_auto_judge_name(task, "some-vm", "original-name"))

    def test_returns_name_unchanged_when_vm_not_in_translation_table(self):
        task = {"task_export_metadata": {"trec-run-id-translation": {"other-vm": {"original-name": "x"}}}}

        self.assertEqual("original-name", _translated_trec_auto_judge_name(task, "some-vm", "original-name"))

    def test_returns_name_unchanged_when_vm_translations_is_not_a_dict(self):
        task = {"task_export_metadata": {"trec-run-id-translation": {"some-vm": "not-a-dict"}}}

        self.assertEqual("original-name", _translated_trec_auto_judge_name(task, "some-vm", "original-name"))

    def test_returns_name_unchanged_when_no_entry_for_name(self):
        task = {"task_export_metadata": {"trec-run-id-translation": {"some-vm": {"other-name": "x"}}}}

        self.assertEqual("original-name", _translated_trec_auto_judge_name(task, "some-vm", "original-name"))


class TestAllowIncompleteTrecAutoJudgeNames(TestCase):
    def test_returns_names_when_entry_exists(self):
        task = {"task_export_metadata": {"allow-incomplete": {"some-vm": ["name-a", "name-b"]}}}

        self.assertEqual({"name-a", "name-b"}, _allow_incomplete_trec_auto_judge_names(task, "some-vm"))

    def test_returns_empty_set_when_task_export_metadata_missing(self):
        self.assertEqual(set(), _allow_incomplete_trec_auto_judge_names({}, "some-vm"))

    def test_returns_empty_set_when_task_export_metadata_is_not_a_dict(self):
        task = {"task_export_metadata": "not-a-dict"}

        self.assertEqual(set(), _allow_incomplete_trec_auto_judge_names(task, "some-vm"))

    def test_returns_empty_set_when_allow_incomplete_field_missing(self):
        task = {"task_export_metadata": {"trec-teams": {"some-vm": "team-42"}}}

        self.assertEqual(set(), _allow_incomplete_trec_auto_judge_names(task, "some-vm"))

    def test_returns_empty_set_when_allow_incomplete_is_not_a_dict(self):
        task = {"task_export_metadata": {"allow-incomplete": "not-a-dict"}}

        self.assertEqual(set(), _allow_incomplete_trec_auto_judge_names(task, "some-vm"))

    def test_returns_empty_set_when_vm_not_in_allow_incomplete(self):
        task = {"task_export_metadata": {"allow-incomplete": {"other-vm": ["name-a"]}}}

        self.assertEqual(set(), _allow_incomplete_trec_auto_judge_names(task, "some-vm"))

    def test_returns_empty_set_when_vm_entry_is_not_a_list(self):
        task = {"task_export_metadata": {"allow-incomplete": {"some-vm": "not-a-list"}}}

        self.assertEqual(set(), _allow_incomplete_trec_auto_judge_names(task, "some-vm"))

    def test_filters_out_non_string_entries(self):
        task = {"task_export_metadata": {"allow-incomplete": {"some-vm": ["name-a", 42, None, "name-b"]}}}

        self.assertEqual({"name-a", "name-b"}, _allow_incomplete_trec_auto_judge_names(task, "some-vm"))


class TestMergeTrecAutoJudgeUploads(TestCase):
    def _upload(self, upload_id, runs, description="description", priority="5", last_edit="2024-01-01"):
        return {
            "id": upload_id,
            "display_name": "some-name",
            "upload_metadata": {"priority": priority},
            "description": description,
            "last_edit": last_edit,
            "runs": runs,
        }

    def test_concatenates_runs_of_a_single_group(self):
        run_a = {"run_id": "run-a", "dataset": "rag26-20260827_1-test", "is_evaluation": False}
        run_b = {"run_id": "run-b", "dataset": "ragtime26-20260827-test", "is_evaluation": False}
        group = [self._upload(1, [run_a]), self._upload(2, [run_b])]

        merged = _merge_trec_auto_judge_uploads("task-1", "some-vm", "some-name", group)

        self.assertEqual([run_a, run_b], merged["runs"])

    def test_uses_metadata_of_most_recently_edited_entry(self):
        group = [
            self._upload(1, [], last_edit="2024-01-01", description="description"),
            self._upload(2, [], last_edit="2024-06-01", description="description"),
        ]

        merged = _merge_trec_auto_judge_uploads("task-1", "some-vm", "some-name", group)

        self.assertEqual(2, merged["id"])

    def test_raises_when_descriptions_differ(self):
        group = [
            self._upload(1, [], description="description A"),
            self._upload(2, [], description="description B"),
        ]

        with self.assertRaises(ExportError) as context:
            _merge_trec_auto_judge_uploads("task-1", "some-vm", "some-name", group)

        message = str(context.exception)
        self.assertIn("some-name", message)
        self.assertIn("some-vm", message)
        self.assertIn("task-1", message)

    def test_raises_when_priorities_differ(self):
        group = [
            self._upload(1, [], priority="5"),
            self._upload(2, [], priority="6"),
        ]

        with self.assertRaises(ExportError):
            _merge_trec_auto_judge_uploads("task-1", "some-vm", "some-name", group)

    def test_does_not_raise_for_a_single_entry_group(self):
        group = [self._upload(1, [])]

        merged = _merge_trec_auto_judge_uploads("task-1", "some-vm", "some-name", group)

        self.assertEqual(1, merged["id"])


class TestTrecAutoJudgeExport(TestCase):
    """Uses mocks for the data layer (model.get_docker_softwares_with_runs) and for the per-run file lookup
    instead of building full database/filesystem fixtures, since _trec_auto_judge_export only orchestrates
    those two seams."""

    # Shared task fixture whose task_export_metadata resolves "some-vm" to an evalbase team id, as required by
    # _evalbase_team_id_for_trec_auto_judge.
    _AUTO_JUDGE_TASK = {"task_name": "AutoJudge", "task_export_metadata": {"trec-teams": {"some-vm": "team-42"}}}

    def _software(self, docker_software_id, display_name, metadata, runs):
        return {
            "docker_software_id": docker_software_id,
            "display_name": display_name,
            "metadata": metadata,
            "runs": runs,
        }

    def _run(self, run_id, dataset, is_evaluation=False):
        return {"run_id": run_id, "dataset": dataset, "is_evaluation": is_evaluation}

    def _upload(self, upload_id, display_name, upload_metadata, runs, description="description", last_edit="2024-01-01"):
        return {
            "id": upload_id,
            "display_name": display_name,
            "upload_metadata": upload_metadata,
            "runs": runs,
            "description": description,
            "last_edit": last_edit,
        }

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_excludes_software_without_qualifying_priority(
        self, get_docker_softwares_with_runs, add_run_to_zip, get_uploads_with_runs
    ):
        get_uploads_with_runs.return_value = []
        get_docker_softwares_with_runs.return_value = [
            self._software(1, "No Metadata", None, [self._run("run-1", "rag26-20260827_1-test")]),
            self._software(2, "Priority Too High", {"priority": "11"}, [self._run("run-2", "rag26-20260827_1-test")]),
            self._software(3, "Priority Zero", {"priority": "0"}, [self._run("run-3", "rag26-20260827_1-test")]),
        ]

        with self.assertRaises(ExportError):
            _trec_auto_judge_export("auto-judge-task", self._AUTO_JUDGE_TASK, "some-vm")

        add_run_to_zip.assert_not_called()

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports._run_output_files")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_includes_qualifying_software_with_zip_and_yaml(
        self, get_docker_softwares_with_runs, add_run_to_zip, run_output_files, get_uploads_with_runs
    ):
        get_uploads_with_runs.return_value = []
        get_docker_softwares_with_runs.return_value = [
            self._software(
                1,
                "xy-hello",
                {"priority": "5"},
                [
                    self._run("run-id-01", "rag26-20260827_1-test"),
                    self._run("run-id-02", "ragtime26-20260827-test"),
                    self._run("run-id-eval", "rag26-20260827_1-test", is_evaluation=True),
                    self._run("run-id-other-dataset", "some-other-dataset"),
                ],
            )
        ]
        run_output_files.return_value = [Path("/ignored/output/file.txt")]

        response = _trec_auto_judge_export("auto-judge-task", self._AUTO_JUDGE_TASK, "some-vm")

        self.assertEqual("application/zip", response["Content-Type"])
        self.assertIn("auto-judge-task-trec-auto-judge-export.zip", response["Content-Disposition"])

        zipf = zipfile.ZipFile(BytesIO(response.content))
        self.assertEqual({"xy-hello.zip", "xy-hello.yaml"}, set(zipf.namelist()))

        metadata = yaml.safe_load(zipf.read("xy-hello.yaml").decode())
        self.assertEqual("xy-hello", metadata["run_id"])
        self.assertEqual("xy-hello.zip", metadata["zip_file"])
        self.assertIn("zip_size_bytes", metadata)
        self.assertIn("zip_md5sum", metadata)
        self.assertEqual("xy-hello", metadata["tira_code_submission"]["display_name"])
        self.assertNotIn("runs", metadata["tira_code_submission"])
        self.assertNotIn("submission", metadata)
        self.assertEqual({"team_id": "team-42"}, metadata["evalbase"])

        # Only the two non-evaluation runs on the configured auto-judge datasets are added to the per-software
        # zip; the evaluation run and the run on an unrelated dataset are skipped.
        calls = [call.args for call in add_run_to_zip.call_args_list]
        self.assertEqual(2, len(calls))
        self.assertEqual(("rag26-20260827_1-test", "some-vm", "run-id-01", "rag26"), calls[0][1:])
        self.assertEqual(("ragtime26-20260827-test", "some-vm", "run-id-02", "ragtime26"), calls[1][1:])

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports._run_output_files")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_translates_submission_name_via_task_export_metadata(
        self, get_docker_softwares_with_runs, add_run_to_zip, run_output_files, get_uploads_with_runs
    ):
        get_uploads_with_runs.return_value = []
        get_docker_softwares_with_runs.return_value = [
            self._software(
                1,
                "xy-hello",
                {"priority": "5"},
                [
                    self._run("run-id-01", "rag26-20260827_1-test"),
                    self._run("run-id-02", "ragtime26-20260827-test"),
                ],
            )
        ]
        run_output_files.return_value = [Path("/ignored/output/file.txt")]
        task = {
            "task_export_metadata": {
                "trec-teams": {"some-vm": "team-42"},
                "trec-run-id-translation": {"some-vm": {"xy-hello": "translated-run"}},
            }
        }

        response = _trec_auto_judge_export("auto-judge-task", task, "some-vm")

        zipf = zipfile.ZipFile(BytesIO(response.content))
        self.assertEqual({"translated-run.zip", "translated-run.yaml"}, set(zipf.namelist()))

        metadata = yaml.safe_load(zipf.read("translated-run.yaml").decode())
        self.assertEqual("translated-run", metadata["run_id"])
        self.assertEqual("translated-run.zip", metadata["zip_file"])
        # The translation only affects the exported run_id/file names, not the embedded submission metadata.
        self.assertEqual("xy-hello", metadata["tira_code_submission"]["display_name"])
        calls = [call.args for call in add_run_to_zip.call_args_list]
        self.assertEqual(2, len(calls))
        self.assertEqual(("rag26-20260827_1-test", "some-vm", "run-id-01", "rag26"), calls[0][1:])
        self.assertEqual(("ragtime26-20260827-test", "some-vm", "run-id-02", "ragtime26"), calls[1][1:])

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports._run_output_files")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_raises_for_software_with_runs_on_only_one_required_dataset(
        self, get_docker_softwares_with_runs, add_run_to_zip, run_output_files, get_uploads_with_runs
    ):
        get_uploads_with_runs.return_value = []
        get_docker_softwares_with_runs.return_value = [
            self._software(
                1,
                "only-one-dataset",
                {"priority": "5"},
                [self._run("run-id-01", "rag26-20260827_1-test")],
            )
        ]
        run_output_files.return_value = [Path("/ignored/output/file.txt")]

        with self.assertRaises(ExportError) as context:
            _trec_auto_judge_export("auto-judge-task", self._AUTO_JUDGE_TASK, "some-vm")

        self.assertIn("only-one-dataset", str(context.exception))

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports._run_output_files")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_raises_for_software_whose_runs_have_no_output_on_disk(
        self, get_docker_softwares_with_runs, add_run_to_zip, run_output_files, get_uploads_with_runs
    ):
        get_uploads_with_runs.return_value = []
        get_docker_softwares_with_runs.return_value = [
            self._software(
                1,
                "no-output-on-disk",
                {"priority": "5"},
                [
                    self._run("run-id-01", "rag26-20260827_1-test"),
                    self._run("run-id-02", "ragtime26-20260827-test"),
                ],
            )
        ]
        run_output_files.return_value = []

        with self.assertRaises(ExportError) as context:
            _trec_auto_judge_export("auto-judge-task", self._AUTO_JUDGE_TASK, "some-vm")

        self.assertIn("no-output-on-disk", str(context.exception))
        add_run_to_zip.assert_not_called()

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports._run_output_files")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_reports_all_submissions_missing_dataset_coverage(
        self, get_docker_softwares_with_runs, add_run_to_zip, run_output_files, get_uploads_with_runs
    ):
        get_uploads_with_runs.return_value = [
            self._upload(1, "upload-missing", {"priority": "5"}, [self._run("run-id-01", "rag26-20260827_1-test")])
        ]
        get_docker_softwares_with_runs.return_value = [
            self._software(
                1, "software-missing", {"priority": "5"}, [self._run("run-id-02", "rag26-20260827_1-test")]
            )
        ]
        run_output_files.return_value = [Path("/ignored/output/file.txt")]

        with self.assertRaises(ExportError) as context:
            _trec_auto_judge_export("auto-judge-task", self._AUTO_JUDGE_TASK, "some-vm")

        message = str(context.exception)
        self.assertIn("software-missing", message)
        self.assertIn("upload-missing", message)

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports._run_output_files")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_allows_incomplete_submission_when_on_allow_list(
        self, get_docker_softwares_with_runs, add_run_to_zip, run_output_files, get_uploads_with_runs
    ):
        task = {
            "task_name": "AutoJudge",
            "task_export_metadata": {
                "trec-teams": {"some-vm": "team-42"},
                "allow-incomplete": {"some-vm": ["only-one-dataset"]},
            },
        }
        get_uploads_with_runs.return_value = []
        get_docker_softwares_with_runs.return_value = [
            self._software(
                1,
                "only-one-dataset",
                {"priority": "5"},
                [self._run("run-id-01", "rag26-20260827_1-test")],
            )
        ]
        run_output_files.return_value = [Path("/ignored/output/file.txt")]

        response = _trec_auto_judge_export("auto-judge-task", task, "some-vm")

        zipf = zipfile.ZipFile(BytesIO(response.content))
        self.assertEqual({"only-one-dataset.zip", "only-one-dataset.yaml"}, set(zipf.namelist()))
        self.assertEqual(1, add_run_to_zip.call_count)

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports._run_output_files")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_reports_only_non_allow_listed_submission_as_incomplete(
        self, get_docker_softwares_with_runs, add_run_to_zip, run_output_files, get_uploads_with_runs
    ):
        task = {
            "task_name": "AutoJudge",
            "task_export_metadata": {
                "trec-teams": {"some-vm": "team-42"},
                "allow-incomplete": {"some-vm": ["allow-listed"]},
            },
        }
        get_uploads_with_runs.return_value = []
        get_docker_softwares_with_runs.return_value = [
            self._software(
                1, "allow-listed", {"priority": "5"}, [self._run("run-id-01", "rag26-20260827_1-test")]
            ),
            self._software(
                2, "not-allow-listed", {"priority": "5"}, [self._run("run-id-02", "rag26-20260827_1-test")]
            ),
        ]
        run_output_files.return_value = [Path("/ignored/output/file.txt")]

        with self.assertRaises(ExportError) as context:
            _trec_auto_judge_export("auto-judge-task", task, "some-vm")

        message = str(context.exception)
        self.assertIn("Submission 'not-allow-listed'", message)
        self.assertNotIn("Submission 'allow-listed'", message)

    @patch("tira_app.endpoints.task_exports._run_output_files")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_excludes_runs_whose_run_id_is_not_a_safe_path_component(
        self, get_docker_softwares_with_runs, get_uploads_with_runs, add_run_to_zip, run_output_files
    ):
        get_uploads_with_runs.return_value = []
        get_docker_softwares_with_runs.return_value = [
            self._software(
                1,
                "valid-sub-name",
                {"priority": "5"},
                [
                    # Contains a path separator, must be skipped (regardless of length/charset, unlike
                    # valid_trec_run_id, which only applies to submission names, not internal run ids).
                    self._run("run/id-01", "rag26-20260827_1-test"),
                    self._run("run/id-02", "ragtime26-20260827-test"),
                ],
            )
        ]
        run_output_files.return_value = [Path("/ignored/output/file.txt")]

        with self.assertRaises(ExportError):
            _trec_auto_judge_export("auto-judge-task", self._AUTO_JUDGE_TASK, "some-vm")

        add_run_to_zip.assert_not_called()

    @patch("tira_app.endpoints.task_exports._run_output_files")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_includes_runs_with_realistic_timestamp_uuid_run_ids(
        self, get_docker_softwares_with_runs, get_uploads_with_runs, add_run_to_zip, run_output_files
    ):
        # Real TIRA run ids (see tira.io_utils.get_tira_id) are timestamp+uuid based and routinely exceed
        # valid_trec_run_id's length limit (which only applies to submission names, not internal run ids).
        get_uploads_with_runs.return_value = []
        get_docker_softwares_with_runs.return_value = [
            self._software(
                1,
                "valid-sub-name",
                {"priority": "5"},
                [
                    self._run("2026-01-01-10-00-00-abcd1234", "rag26-20260827_1-test"),
                    self._run("2026-01-01-10-00-00-abcd1234-rerank-2026-01-02-11-00-00-efgh5678", "ragtime26-20260827-test"),
                ],
            )
        ]
        run_output_files.return_value = [Path("/ignored/output/file.txt")]

        response = _trec_auto_judge_export("auto-judge-task", self._AUTO_JUDGE_TASK, "some-vm")

        zipf = zipfile.ZipFile(BytesIO(response.content))
        self.assertEqual({"valid-sub-name.zip", "valid-sub-name.yaml"}, set(zipf.namelist()))
        self.assertEqual(2, add_run_to_zip.call_count)

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_reports_qualifying_submission_with_invalid_name_as_error(
        self, get_docker_softwares_with_runs, add_run_to_zip, get_uploads_with_runs
    ):
        get_uploads_with_runs.return_value = []
        get_docker_softwares_with_runs.return_value = [
            # Display name contains a space, so it is not a valid_trec_run_id even though it otherwise qualifies
            # (priority metadata present; would not even reach the dataset-coverage check).
            self._software(1, "Invalid Name", {"priority": "5"}, [self._run("run-id-01", "rag26-20260827_1-test")])
        ]

        with self.assertRaises(ExportError) as context:
            _trec_auto_judge_export("auto-judge-task", self._AUTO_JUDGE_TASK, "some-vm")

        self.assertIn("Invalid Name", str(context.exception))
        add_run_to_zip.assert_not_called()

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports._run_output_files")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_reports_all_invalid_names_and_still_includes_valid_submissions(
        self, get_docker_softwares_with_runs, add_run_to_zip, run_output_files, get_uploads_with_runs
    ):
        get_uploads_with_runs.return_value = [
            self._upload(1, "Upload With Space", {"priority": "5"}, [self._run("run-id-01", "rag26-20260827_1-test")])
        ]
        get_docker_softwares_with_runs.return_value = [
            self._software(
                1, "Software With Space", {"priority": "5"}, [self._run("run-id-01", "rag26-20260827_1-test")]
            ),
            self._software(
                2,
                "valid-software",
                {"priority": "5"},
                [
                    self._run("run-id-02", "rag26-20260827_1-test"),
                    self._run("run-id-03", "ragtime26-20260827-test"),
                ],
            ),
        ]
        run_output_files.return_value = [Path("/ignored/output/file.txt")]

        with self.assertRaises(ExportError) as context:
            _trec_auto_judge_export("auto-judge-task", self._AUTO_JUDGE_TASK, "some-vm")

        message = str(context.exception)
        self.assertIn("Software With Space", message)
        self.assertIn("Upload With Space", message)
        # The otherwise-valid submission must not have been bundled since the whole export fails together.
        add_run_to_zip.assert_not_called()

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_handles_no_qualifying_software(self, get_docker_softwares_with_runs, get_uploads_with_runs):
        get_docker_softwares_with_runs.return_value = []
        get_uploads_with_runs.return_value = []

        with self.assertRaises(ExportError):
            _trec_auto_judge_export("auto-judge-task", self._AUTO_JUDGE_TASK, "some-vm")

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_fails_before_querying_submissions_when_vm_has_no_evalbase_team_id(
        self, get_docker_softwares_with_runs, get_uploads_with_runs
    ):
        task = {"task_name": "AutoJudge", "task_export_metadata": {"trec-teams": {"other-vm": "team-42"}}}

        with self.assertRaises(ExportError):
            _trec_auto_judge_export("auto-judge-task", task, "some-vm")

        get_docker_softwares_with_runs.assert_not_called()
        get_uploads_with_runs.assert_not_called()

    @patch("tira_app.endpoints.task_exports._run_output_files")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_includes_qualifying_upload_with_zip_and_yaml(
        self, get_docker_softwares_with_runs, get_uploads_with_runs, add_run_to_zip, run_output_files
    ):
        get_docker_softwares_with_runs.return_value = []
        get_uploads_with_runs.return_value = [
            self._upload(
                1,
                "xy-upload",
                {"priority": "5"},
                [
                    self._run("run-id-01", "rag26-20260827_1-test"),
                    self._run("run-id-02", "ragtime26-20260827-test"),
                ],
            )
        ]
        run_output_files.return_value = [Path("/ignored/output/file.txt")]

        response = _trec_auto_judge_export("auto-judge-task", self._AUTO_JUDGE_TASK, "some-vm")

        zipf = zipfile.ZipFile(BytesIO(response.content))
        self.assertEqual({"xy-upload.zip", "xy-upload.yaml"}, set(zipf.namelist()))

        metadata = yaml.safe_load(zipf.read("xy-upload.yaml").decode())
        self.assertEqual("xy-upload", metadata["run_id"])
        self.assertEqual("xy-upload.zip", metadata["zip_file"])
        self.assertEqual("xy-upload", metadata["tira_upload_submission"]["display_name"])
        self.assertNotIn("runs", metadata["tira_upload_submission"])
        self.assertNotIn("tira_code_submission", metadata)
        self.assertEqual({"team_id": "team-42"}, metadata["evalbase"])

    @patch("tira_app.endpoints.task_exports._run_output_files")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_excludes_upload_without_qualifying_priority(
        self, get_docker_softwares_with_runs, get_uploads_with_runs, add_run_to_zip, run_output_files
    ):
        get_docker_softwares_with_runs.return_value = []
        get_uploads_with_runs.return_value = [
            self._upload(1, "no-priority-upload", None, [self._run("run-id-01", "rag26-20260827_1-test")]),
        ]
        run_output_files.return_value = [Path("/ignored/output/file.txt")]

        with self.assertRaises(ExportError):
            _trec_auto_judge_export("auto-judge-task", self._AUTO_JUDGE_TASK, "some-vm")

        add_run_to_zip.assert_not_called()

    @patch("tira_app.endpoints.task_exports._run_output_files")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_includes_both_qualifying_docker_software_and_upload(
        self, get_docker_softwares_with_runs, get_uploads_with_runs, add_run_to_zip, run_output_files
    ):
        get_docker_softwares_with_runs.return_value = [
            self._software(
                1,
                "xy-hello",
                {"priority": "5"},
                [
                    self._run("run-id-01", "rag26-20260827_1-test"),
                    self._run("run-id-02", "ragtime26-20260827-test"),
                ],
            )
        ]
        get_uploads_with_runs.return_value = [
            self._upload(
                1,
                "xy-upload",
                {"priority": "5"},
                [
                    self._run("run-id-03", "rag26-20260827_1-test"),
                    self._run("run-id-04", "ragtime26-20260827-test"),
                ],
            )
        ]
        run_output_files.return_value = [Path("/ignored/output/file.txt")]

        response = _trec_auto_judge_export("auto-judge-task", self._AUTO_JUDGE_TASK, "some-vm")

        zipf = zipfile.ZipFile(BytesIO(response.content))
        self.assertEqual(
            {"xy-hello.zip", "xy-hello.yaml", "xy-upload.zip", "xy-upload.yaml"},
            set(zipf.namelist()),
        )

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_reports_error_when_docker_software_and_upload_share_a_name(
        self, get_docker_softwares_with_runs, add_run_to_zip, get_uploads_with_runs
    ):
        get_docker_softwares_with_runs.return_value = [
            self._software(
                1, "same-name", {"priority": "5"}, [self._run("run-id-01", "rag26-20260827_1-test")]
            )
        ]
        get_uploads_with_runs.return_value = [
            self._upload(1, "same-name", {"priority": "5"}, [self._run("run-id-02", "ragtime26-20260827-test")])
        ]

        with self.assertRaises(ExportError) as context:
            _trec_auto_judge_export("auto-judge-task", self._AUTO_JUDGE_TASK, "some-vm")

        self.assertIn("same-name", str(context.exception))
        add_run_to_zip.assert_not_called()

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports._run_output_files")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_merges_uploads_sharing_a_name_across_datasets(
        self, get_docker_softwares_with_runs, add_run_to_zip, run_output_files, get_uploads_with_runs
    ):
        get_docker_softwares_with_runs.return_value = []
        get_uploads_with_runs.return_value = [
            self._upload(
                1, "shared-name", {"priority": "5"}, [self._run("run-id-01", "rag26-20260827_1-test")]
            ),
            self._upload(
                2, "shared-name", {"priority": "5"}, [self._run("run-id-02", "ragtime26-20260827-test")]
            ),
        ]
        run_output_files.return_value = [Path("/ignored/output/file.txt")]

        response = _trec_auto_judge_export("auto-judge-task", self._AUTO_JUDGE_TASK, "some-vm")

        zipf = zipfile.ZipFile(BytesIO(response.content))
        self.assertEqual({"shared-name.zip", "shared-name.yaml"}, set(zipf.namelist()))
        calls = [call.args for call in add_run_to_zip.call_args_list]
        self.assertEqual(2, len(calls))

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports._add_run_to_zip")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_reports_error_when_uploads_sharing_a_name_have_differing_description(
        self, get_docker_softwares_with_runs, add_run_to_zip, get_uploads_with_runs
    ):
        get_docker_softwares_with_runs.return_value = []
        get_uploads_with_runs.return_value = [
            self._upload(
                1,
                "shared-name",
                {"priority": "5"},
                [self._run("run-id-01", "rag26-20260827_1-test")],
                description="description A",
            ),
            self._upload(
                2,
                "shared-name",
                {"priority": "5"},
                [self._run("run-id-02", "ragtime26-20260827-test")],
                description="description B",
            ),
        ]

        with self.assertRaises(ExportError) as context:
            _trec_auto_judge_export("auto-judge-task", self._AUTO_JUDGE_TASK, "some-vm")

        self.assertIn("shared-name", str(context.exception))
        add_run_to_zip.assert_not_called()


class TestTrecAutoJudgeExportEndpoint(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()

    def setUp(self):
        modeldb.Task.objects.filter(task_id="shared-task-1").update(
            export_buttons=json.dumps([{"display_name": "AutoJudge Export", "value": "trec-auto-judge"}]),
            task_export_metadata=json.dumps({"trec-teams": {"master-vm-for-task-1": "team-42"}}),
        )

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_admin_gets_400_with_message_when_export_would_be_empty(
        self, get_docker_softwares_with_runs, get_uploads_with_runs
    ):
        get_docker_softwares_with_runs.return_value = []
        get_uploads_with_runs.return_value = []

        response = task_export(
            _request(ADMIN), task_id="shared-task-1", vm_id="master-vm-for-task-1", value="trec-auto-judge"
        )

        self.assertEqual(400, response.status_code)
        content = json.loads(response.content)
        self.assertIn("would be empty", content["message"])
        get_docker_softwares_with_runs.assert_called_once_with(
            "shared-task-1", "master-vm-for-task-1", return_code_submissions=True
        )

    def test_admin_gets_400_with_message_when_vm_has_no_evalbase_team_id(self):
        modeldb.Task.objects.filter(task_id="shared-task-1").update(
            task_export_metadata=json.dumps({"trec-teams": {"some-other-vm": "team-42"}})
        )

        response = task_export(
            _request(ADMIN), task_id="shared-task-1", vm_id="master-vm-for-task-1", value="trec-auto-judge"
        )

        self.assertEqual(400, response.status_code)
        content = json.loads(response.content)
        self.assertIn("master-vm-for-task-1", content["message"])
        self.assertIn("trec-teams", content["message"])

    @patch("tira_app.endpoints.task_exports.model.get_uploads_with_runs")
    @patch("tira_app.endpoints.task_exports.model.get_docker_softwares_with_runs")
    def test_admin_can_download_trec_auto_judge_export_with_qualifying_submission(
        self, get_docker_softwares_with_runs, get_uploads_with_runs
    ):
        from django.conf import settings

        get_uploads_with_runs.return_value = []
        get_docker_softwares_with_runs.return_value = [
            {
                "docker_software_id": 1,
                "display_name": "xy-hello",
                "metadata": {"priority": "5"},
                "runs": [
                    {"run_id": "run-id-01", "dataset": "rag26-20260827_1-test", "is_evaluation": False},
                    {"run_id": "run-id-02", "dataset": "ragtime26-20260827-test", "is_evaluation": False},
                ],
            }
        ]
        for dataset, run_id in (
            ("rag26-20260827_1-test", "run-id-01"),
            ("ragtime26-20260827-test", "run-id-02"),
        ):
            run_output_dir = settings.TIRA_ROOT / "data" / "runs" / dataset / "master-vm-for-task-1" / run_id / "output"
            run_output_dir.mkdir(parents=True, exist_ok=True)
            (run_output_dir / "run.txt").write_text("output")

        response = task_export(
            _request(ADMIN), task_id="shared-task-1", vm_id="master-vm-for-task-1", value="trec-auto-judge"
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/zip", response["Content-Type"])
        zipf = zipfile.ZipFile(BytesIO(response.content))
        self.assertEqual({"xy-hello.zip", "xy-hello.yaml"}, set(zipf.namelist()))
