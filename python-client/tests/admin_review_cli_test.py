import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import tira.admin_review_agent as agent
from tira import tira_cli
from tira.admin_review_agent import run_review_agent
from tira.rest_api_client import Client

ENVIRONMENT = {k: "x" for k in agent.REQUIRED_ENVIRONMENT_VARIABLES}
ENVIRONMENT["COPILOT_PROVIDER_BASE_URL"] = "https://llm.example.org/v1"


def review_directory_with_batches(count):
    directory = Path(tempfile.mkdtemp())
    for i in range(count):
        batch = directory / "batches" / f"{i:04d}"
        batch.mkdir(parents=True)
        (batch / "README.md").write_text("readme")
        (batch / "manifest.json").write_text(json.dumps({"runs": [], "example_runs": []}))
    return directory


class FakeDocker:
    """A docker client whose containers exit with the given codes (one per batch)."""

    def __init__(self, exit_codes):
        self.exit_codes = list(exit_codes)
        self.started = []
        self.images = MagicMock()
        self.containers = MagicMock()
        self.containers.run.side_effect = self.run

    def run(self, image, **kwargs):
        self.started.append(kwargs)
        container = MagicMock()
        container.wait.return_value = {"StatusCode": self.exit_codes[len(self.started) - 1]}
        container.logs.return_value = f"log of container {len(self.started)}".encode()
        return container


class RunReviewAgentTest(unittest.TestCase):
    def run_agent(self, directory, exit_codes, **kwargs):
        docker = FakeDocker(exit_codes)
        proxy = MagicMock()
        proxy.environment_variables = {}
        with patch("docker.from_env", return_value=docker), patch(
            "tira.network_proxy.start_network_proxy", return_value=proxy
        ):
            output = run_review_agent(directory, environment=ENVIRONMENT, **kwargs)
        return docker, proxy, output

    def test_one_container_per_batch_with_callback_after_each_batch(self):
        directory = review_directory_with_batches(2)
        calls = []

        docker, proxy, output = self.run_agent(directory, [0, 0], on_batch_done=lambda b, o: calls.append((b.name, o)))

        self.assertEqual(2, len(docker.started))
        self.assertEqual([("0000", output), ("0001", output)], calls)
        self.assertEqual(output, directory.resolve() / "agent-output")
        self.assertIn("log of container 2", (output / "agent-log.txt").read_text())
        proxy.stop.assert_called_once()
        for kwargs in docker.started:
            binds = {v["bind"]: v["mode"] for v in kwargs["volumes"].values()}
            self.assertEqual("rw", binds["/tira-data/output"])
            self.assertEqual("ro", binds["/tira-data/input/manifest.json"])

    def test_failing_batch_and_failing_callback_do_not_stop_later_batches(self):
        directory = review_directory_with_batches(3)
        calls = []

        def callback(batch, output):
            calls.append(batch.name)
            raise RuntimeError("upload failed")

        docker, _, _ = self.run_agent(directory, [1, 0, 0], on_batch_done=callback)

        self.assertEqual(3, len(docker.started))
        self.assertEqual(["0000", "0001", "0002"], calls)

    def test_configured_output_directory_is_not_cleared_but_the_default_is(self):
        directory = review_directory_with_batches(1)
        custom = Path(tempfile.mkdtemp())
        (custom / "old.txt").write_text("keep")
        (directory / "agent-output").mkdir()
        (directory / "agent-output" / "old.txt").write_text("remove")

        self.run_agent(directory, [0], output_directory=custom)
        self.assertTrue((custom / "old.txt").exists())

        self.run_agent(directory, [0])
        self.assertFalse((directory / "agent-output" / "old.txt").exists())

    def test_without_batches_no_container_is_started(self):
        docker, _, output = self.run_agent(Path(tempfile.mkdtemp()), [])

        self.assertEqual([], docker.started)
        self.assertEqual("", (output / "agent-log.txt").read_text())

    def test_missing_environment_variables(self):
        with self.assertRaises(ValueError):
            run_review_agent(review_directory_with_batches(1), environment={})


class FakeCli:
    """Patches everything that talks to TIRA or docker for the admin review commands."""

    def __init__(self, test):
        self.messages = []
        self.client = MagicMock()
        patches = [
            patch.dict("os.environ", ENVIRONMENT),
            patch("tira.tira_cli.RestClient", return_value=self.client),
            patch("tira.tira_cli.clean_logger", return_value=lambda m, level=None: self.messages.append(m)),
        ]
        for p in patches:
            p.start()
            test.addCleanup(p.stop)


def valid_software_review(verdict="no_concerns"):
    ok = {"status": "ok", "summary": "s", "evidence": []}
    return {
        "description": "d",
        "verdict": verdict,
        "comment": "c",
        "hacking_attempt": ok,
        "data_leak_attempt": ok,
        "malicious_behavior": ok,
        "key_snippets": [],
        "external_endpoints": [],
        "dependencies": [],
        "files_accessed": [],
        "environment_variables": [],
        "models_and_data": [],
    }


class AdminReviewSoftwareCliTest(unittest.TestCase):
    def setUp(self):
        self.cli = FakeCli(self)
        self.cli.client.private_system_details.return_value = {"docker_software_id": 7}
        self.cli.client.software_reviews.return_value = []
        self.directory = Path(tempfile.mkdtemp())
        self.agent_calls = 0

    def review(self, verdict="no_concerns", **kwargs):
        def fake_agent(directory, timeout, output_directory=None):
            self.agent_calls += 1
            output = Path(tempfile.mkdtemp())
            (output / "reviews" / "team").mkdir(parents=True)
            (output / "reviews" / "team" / "sw.json").write_text(json.dumps(valid_software_review(verdict)))
            return output

        manifest = {"team": "team", "software": "sw", "image": "i", "command": "c"}
        with patch(
            "tira.admin_review_software.prepare_software_review_directory", return_value=(self.directory, manifest)
        ), patch("tira.admin_review_agent.run_review_agent", fake_agent), patch(
            "tira.admin_review_software.upload_software_review", return_value={"id": "uuid"}
        ) as upload:
            code = tira_cli.admin_review_software("task", "team", "sw", **kwargs)
        return code, upload

    def test_existing_review_is_shown_like_a_fresh_one_from_the_cached_zip(self):
        self.cli.client.software_reviews.return_value = [
            {"id": "u", "review_date": "2026-01-01T00:00", "verdict": "no_concerns", "details": {"llm": "gpt"}}
        ]

        def download(docker_software_id, review_id, target):
            target.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(target, "w") as z:
                z.writestr("reviews/team/sw.json", json.dumps(valid_software_review("no_concerns")))

        self.cli.client.download_software_review.side_effect = download
        target = self.directory / "out"
        self.cli.client.tira_cache_dir = str(self.directory / "cache")

        with patch("builtins.print") as printed:
            code, upload = self.review(output=str(target))

        self.assertEqual((0, 0), (code, self.agent_calls))
        upload.assert_not_called()
        self.assertIn("Result:", printed.call_args[0][0])
        self.assertIn(str(target), printed.call_args[0][0])
        self.assertTrue((self.directory / "cache" / "software-reviews" / "u.zip").is_file())

    def test_without_team_and_software_all_softwares_of_the_task_are_reviewed(self):
        self.cli.client.docker_softwares_of_task.return_value = [
            {"team": "a", "display_name": "s1", "automatic_review_count": 1},
            {"team": "b", "display_name": "s2", "automatic_review_count": 0},
        ]

        with patch("tira.tira_cli._review_software", side_effect=[0, 1]) as single, patch(
            "tira.tira_cli.time.sleep"
        ) as sleep, patch("builtins.print") as printed:
            code = tira_cli.admin_review_software("task", output="/o", agent_output=None, force=True)

        self.assertEqual(1, code)
        self.assertEqual([call(10), call(10)], sleep.call_args_list)
        overview = " ".join(c[0][0] for c in printed.call_args_list)
        self.assertIn("2 submissions: 1 already reviewed, 2 to be reviewed now", overview)
        self.assertIn("software 2 of 2 (b/s2) will be reviewed in 10 seconds", printed.call_args[0][0])
        self.assertEqual(
            [("task", "a", "s1", "/o/a/s1", None), ("task", "b", "s2", "/o/b/s2", None)],
            [c[0] for c in single.call_args_list],
        )

    def test_team_without_software_is_rejected(self):
        self.assertEqual(1, tira_cli.admin_review_software("task", team="a"))

    def test_force_adds_a_new_review_even_if_one_exists(self):
        self.cli.client.software_reviews.return_value = [{"id": "u"}]

        code, upload = self.review(force=True)

        self.assertEqual((0, 1), (code, self.agent_calls))
        upload.assert_called_once()
        self.assertEqual(7, upload.call_args[0][1])

    def test_review_without_concerns_is_uploaded(self):
        code, upload = self.review()

        self.assertEqual(0, code)
        upload.assert_called_once()
        self.assertTrue(any("uploaded to TIRA" in m for m in self.cli.messages))

    def test_review_that_needs_a_human_is_uploaded(self):
        code, upload = self.review(verdict="needs_human_review")

        self.assertEqual(0, code)
        upload.assert_called_once()

    def test_no_upload(self):
        code, upload = self.review(no_upload=True)

        self.assertEqual(0, code)
        upload.assert_not_called()

    def test_failing_upload_fails(self):
        with patch("tira.admin_review_software.upload_software_review", side_effect=RuntimeError("no")):
            manifest = {"team": "team", "software": "sw"}
            with patch(
                "tira.admin_review_software.prepare_software_review_directory", return_value=(self.directory, manifest)
            ), patch("tira.admin_review_agent.run_review_agent") as run_agent:
                output = Path(tempfile.mkdtemp())
                (output / "reviews" / "team").mkdir(parents=True)
                (output / "reviews" / "team" / "sw.json").write_text(json.dumps(valid_software_review()))
                run_agent.return_value = output
                code = tira_cli.admin_review_software("task", "team", "sw")

        self.assertEqual(1, code)

    def test_missing_environment_variables(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(1, tira_cli.admin_review_software("task", "team", "sw"))

    def test_failing_lookup_fails(self):
        self.cli.client.software_reviews.side_effect = RuntimeError("down")

        self.assertEqual(1, tira_cli.admin_review_software("task", "team", "sw"))


def valid_run_review(evaluations=()):
    ok = {"status": "ok", "summary": "s"}
    return {
        "verdict": "valid",
        "output_reasonable": ok,
        "software_failure": ok,
        "hacking_attempt": ok,
        "data_leak_attempt": ok,
        "tira_review": {"no_errors": True, "output_error": False, "software_error": False, "comment": "fine"},
        "evaluations": [{"run_id": e, "status": "ok"} for e in evaluations],
    }


class AdminReviewRunsCliTest(unittest.TestCase):
    def setUp(self):
        self.cli = FakeCli(self)
        self.directory = Path(tempfile.mkdtemp())
        run = {"dataset": "d", "team": "t", "run_id": "r1", "only_evaluations": False, "evaluations": []}
        (self.directory / "manifest.json").write_text(json.dumps({"runs": [run]}))
        self.batch = self.directory / "batches" / "0000"
        self.batch.mkdir(parents=True)
        (self.batch / "manifest.json").write_text(json.dumps({"runs": [run], "example_runs": []}))
        self.run = run

    def review(self, review, **kwargs):
        def fake_agent(directory, timeout, output_directory=None, on_batch_done=None):
            output = Path(tempfile.mkdtemp())
            (output / "reviews" / "d" / "t").mkdir(parents=True)
            (output / "reviews" / "d" / "t" / "r1.json").write_text(json.dumps(review))
            on_batch_done(self.batch, output)
            return output

        with patch("tira.admin_review_runs.prepare_review_directory", return_value=(self.directory, [self.run])), patch(
            "tira.admin_review_agent.run_review_agent", fake_agent
        ), patch("builtins.print"):
            return tira_cli.admin_review_runs("task", **kwargs)

    def test_valid_reviews_are_uploaded_after_the_batch(self):
        self.assertEqual(0, self.review(valid_run_review()))

        self.cli.client.review_run.assert_called_once_with("r1", "d", "t", True, False, False, "fine")

    def test_no_upload(self):
        self.assertEqual(0, self.review(valid_run_review(), no_upload=True))

        self.cli.client.review_run.assert_not_called()

    def test_invalid_review_fails_and_is_not_uploaded(self):
        self.assertEqual(1, self.review({"verdict": "valid"}))

        self.cli.client.review_run.assert_not_called()

    def test_no_unreviewed_runs_does_not_start_the_agent(self):
        with patch("tira.admin_review_runs.prepare_review_directory", return_value=(self.directory, [])), patch(
            "tira.admin_review_agent.run_review_agent"
        ) as run_agent:
            self.assertEqual(0, tira_cli.admin_review_runs("task"))

        run_agent.assert_not_called()

    def test_not_enough_example_runs_fails(self):
        with patch("tira.admin_review_runs.prepare_review_directory", side_effect=ValueError("only 1 run")), patch(
            "tira.admin_review_agent.run_review_agent"
        ) as run_agent:
            self.assertEqual(1, tira_cli.admin_review_runs("task"))

        run_agent.assert_not_called()


class RestClientSoftwareReviewTest(unittest.TestCase):
    def client(self):
        client = Client.__new__(Client)
        client.base_url = "https://tira.example.org"
        client.verify = True
        client.failsave_retries = 1
        client.failsave_max_delay = 1
        client.get_csrf_token = lambda: "csrf"
        client.authentication_headers = lambda url=None: {"Api-Key": "key"}
        return client

    def test_list_reviews(self):
        client = self.client()
        client.json_response = MagicMock(return_value={"context": {"reviews": [{"id": "u"}]}})

        self.assertEqual([{"id": "u"}], client.software_reviews(7))
        client.json_response.assert_called_once_with("/v1/admin/docker-software-automatic-reviews/7")

    def test_upload_sends_the_zip_and_the_form_fields_and_accepts_201(self):
        client = self.client()
        zip_file = Path(tempfile.mkdtemp()) / "review.zip"
        zip_file.write_bytes(b"PK")
        response = MagicMock(status_code=201)
        response.json.return_value = {"status": 0, "context": {"id": "uuid"}}

        with patch("requests.post", return_value=response) as post:
            ret = client.upload_software_review(7, "title", "no_concerns", "comment", {"llm": "m"}, zip_file)

        self.assertEqual({"id": "uuid"}, ret)
        kwargs = post.call_args[1]
        self.assertEqual("https://tira.example.org/v1/admin/docker-software-automatic-reviews/7", kwargs["url"])
        self.assertEqual(["file"], list(kwargs["files"]))
        self.assertEqual(
            {"title": "title", "verdict": "no_concerns", "comment": "comment", "details": '{"llm": "m"}'},
            kwargs["data"],
        )
        self.assertEqual("key", kwargs["headers"]["Api-Key"])
