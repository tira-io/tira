import io
import json
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import tira.admin_review_software as software
from tira.admin_review_software import (
    CHECKS,
    LIST_FIELDS,
    extract_image_metadata,
    extraction_summary,
    format_existing_reviews,
    format_software_result,
    load_software_review,
    package_review,
    prepare_software_review_directory,
    security_summary,
    upload_software_review,
)
from tira.rest_api_client import Client


def add_file(archive, name, content):
    info = tarfile.TarInfo(name)
    info.size = len(content)
    archive.addfile(info, io.BytesIO(content))


def docker_image(path: Path):
    layer = io.BytesIO()
    with tarfile.open(fileobj=layer, mode="w") as layer_tar:
        add_file(layer_tar, "app/run.py", b"print(1)\n")
        add_file(layer_tar, "app/with\ttab.txt", b"x")

    with tarfile.open(path, "w") as image:
        add_file(image, "manifest.json", json.dumps([{"Config": "c.json", "Layers": ["l0/layer.tar"]}]).encode())
        config = {"config": {"Cmd": ["python"]}, "history": [{"created_by": "ADD app /app"}]}
        add_file(image, "c.json", json.dumps(config).encode())
        add_file(image, "l0/layer.tar", layer.getvalue())


def valid_review(**overrides):
    review = {
        "description": "Does something.",
        "verdict": "no_concerns",
        "comment": "fine",
        **{c: {"status": "ok", "summary": "s", "evidence": []} for c in CHECKS},
        **{f: [] for f in LIST_FIELDS},
    }
    review.update(overrides)
    return review


class ExtractImageMetadataTest(unittest.TestCase):
    def test_lists_layers_and_files_without_extracting_them(self):
        directory = Path(tempfile.mkdtemp())
        docker_image(directory / "image.tar")

        result = extract_image_metadata(directory / "image.tar", directory / "extracted")

        self.assertEqual({"layers": 1, "files": 2}, result)
        names = sorted(p.name for p in (directory / "extracted").iterdir())
        self.assertEqual(["files.tsv", "image-config.json", "layers.json"], names)
        files = (directory / "extracted" / "files.tsv").read_text().splitlines()
        self.assertEqual("layer\tsize\tpath", files[0])
        self.assertIn("0\t9\tapp/run.py", files)
        self.assertEqual(
            "ADD app /app", json.loads((directory / "extracted" / "layers.json").read_text())[0]["created_by"]
        )
        self.assertFalse((directory / "extracted" / "app").exists())


class LoadSoftwareReviewTest(unittest.TestCase):
    def setUp(self):
        self.output = Path(tempfile.mkdtemp())
        self.directory = self.output / "reviews" / "team"
        self.directory.mkdir(parents=True)

    def load(self, review):
        (self.directory / "sw.json").write_text(review if isinstance(review, str) else json.dumps(review))
        return load_software_review(self.output, "task", "team", "sw")

    def test_missing_and_invalid_files(self):
        self.assertIn("missing review file", load_software_review(self.output, "t", "team", "sw")["problems"][0])
        self.assertIn("invalid JSON", self.load("{")["problems"][0])

    def test_valid_review(self):
        self.assertEqual([], self.load(valid_review())["problems"])

    def test_problems(self):
        review = valid_review(description=" ", verdict="maybe", key_snippets="x")
        review["hacking_attempt"] = {"status": "suspicious", "summary": "s", "evidence": []}
        del review["data_leak_attempt"]

        problems = self.load(review)["problems"]

        self.assertEqual(5, len(problems))

    def test_snippet_files_must_exist_inside_the_snippets_directory_and_are_packaged(self):
        snippets = self.directory / "sw-snippets" / "app"
        snippets.mkdir(parents=True)
        (snippets / "run.py").write_text("print(1)")

        ok = self.load(valid_review(key_snippets=[{"snippet_file": "app/run.py"}]))
        self.assertEqual([], ok["problems"])
        with tarfile.open(self.directory / "sw-snippets.tar.gz") as archive:
            self.assertIn("sw-snippets/app/run.py", archive.getnames())

        bad = self.load(valid_review(key_snippets=[{"snippet_file": "../x"}, {"snippet_file": "nope.py"}]))
        self.assertEqual(2, len(bad["problems"]))


class SummaryTest(unittest.TestCase):
    def test_security_summary(self):
        result = {"review": valid_review(), "problems": []}
        self.assertEqual("no concern", security_summary(result))

        suspicious = valid_review(verdict="needs_human_review", hacking_attempt={"status": "suspicious"})
        self.assertEqual(
            "needs human review (hacking_attempt: suspicious)", security_summary({"review": suspicious, "problems": []})
        )
        self.assertIn("unknown", security_summary({"review": None, "problems": ["x"]}))
        self.assertIn("unknown", security_summary({"review": valid_review(), "problems": ["x"]}))

    def test_extraction_summary_counts_lists(self):
        review = valid_review(key_snippets=[1, 2], dependencies=[1])
        self.assertTrue(extraction_summary(review).startswith("2 code snippets, 0 external endpoints, 1 dependencies"))

    def test_result_block_is_short(self):
        review = valid_review(description="word " * 500, comment="c " * 500)
        lines = format_software_result(
            {"review": review, "problems": []}, Path("/x/r.json"), Path("/x/agent-output/log")
        )

        self.assertEqual("Result:", lines[0])
        self.assertTrue(lines[1].endswith("no concern"))
        self.assertLess(len(lines), 12)
        self.assertTrue(all(len(line) <= 110 for line in lines))
        self.assertEqual("  Details:     /x", lines[-1])

    def test_existing_reviews(self):
        lines = format_existing_reviews(
            [
                {
                    "id": "abc",
                    "review_date": "2026-11-22T13:00:00.1",
                    "verdict": "needs_human_review",
                    "title": "Automatic review of sw",
                    "comment": "look at it",
                    "details": {"llm": "model-x"},
                }
            ]
        )

        self.assertIn("2026-11-22 13:00  needs human review  [model-x]  abc", lines[0])
        self.assertTrue(any("look at it" in line for line in lines))


class PrepareAndUploadTest(unittest.TestCase):
    def prepare(self, details):
        client = MagicMock()
        client.private_system_details.return_value = details
        log = []

        def fake_download(client, task, team, image, target):
            docker_image(target)

        with patch.object(software, "_download_image", fake_download):
            output = Path(tempfile.mkdtemp())
            directory, manifest = prepare_software_review_directory(
                client, "task", "team", "sw", output, log=log.append
            )
        return directory, manifest, log

    def test_prepare_writes_metadata_extracted_files_and_the_single_batch(self):
        directory, manifest, log = self.prepare(
            {"docker_software_id": 7, "public_image_name": "img:1", "command": "run it"}
        )

        self.assertEqual(7, manifest["docker_software_id"])
        self.assertEqual("img:1", manifest["image"])
        self.assertEqual(["software"], manifest["input_paths"])
        self.assertEqual("Metadata is downloaded", log[0])
        self.assertIn("Docker image is downloaded and extracted", log[1])
        self.assertTrue((directory / "software" / "metadata.json").is_file())
        self.assertTrue((directory / "software" / "extracted" / "files.tsv").is_file())
        batch = json.loads((directory / "batches" / "0000" / "manifest.json").read_text())
        self.assertEqual([], batch["runs"])
        readme = (directory / "batches" / "0000" / "README.md").read_text()
        self.assertIn("`sw` of team `team` on task `task`", readme)
        self.assertNotIn("@", readme.replace("@github", ""))

    def test_docker_software_id_of(self):
        client = MagicMock()
        client.private_system_details.return_value = {"docker_software_id": 7}

        self.assertEqual(7, software.docker_software_id_of(client, "task", "team", "sw"))
        client.private_system_details.assert_called_once_with("task/team/sw")

    def test_prepare_fails_without_docker_image(self):
        with self.assertRaises(ValueError):
            self.prepare({"docker_software_id": 7})

    def test_package_and_upload(self):
        directory, manifest, _ = self.prepare({"docker_software_id": 7, "public_image_name": "img:1"})
        agent_output = Path(tempfile.mkdtemp())
        review_directory = agent_output / "reviews" / "team"
        (review_directory / "sw-snippets").mkdir(parents=True)
        (review_directory / "sw.json").write_text("{}")
        (review_directory / "sw-snippets.tar.gz").write_text("duplicate of the snippets directory")
        (agent_output / "agent-log.txt").write_text("log")

        archive = package_review(
            directory, agent_output, "team", "sw", Path(tempfile.mkdtemp()) / "r.zip", {"llm": "m"}
        )

        names = zipfile.ZipFile(archive).namelist()
        self.assertIn("reviews/team/sw.json", names)
        self.assertIn("agent-log.txt", names)
        self.assertIn("software/extracted/files.tsv", names)
        self.assertIn("software/metadata.json", names)
        self.assertEqual({"llm": "m"}, json.loads(zipfile.ZipFile(archive).read("review-info.json")))
        self.assertFalse(any(n.endswith(".tar.gz") for n in names))

        client = MagicMock()
        client.upload_software_review.return_value = {"id": "uuid"}
        review = valid_review(key_snippets=[1])
        with patch.dict("os.environ", {"COPILOT_MODEL": "model-x"}):
            upload_software_review(client, 7, directory, agent_output, {"review": review, "problems": []}, manifest)

        docker_software_id, title, verdict, comment, details, file_path = client.upload_software_review.call_args[0]
        self.assertEqual(
            (7, "Automatic review of sw", "no_concerns", "fine"), (docker_software_id, title, verdict, comment)
        )
        self.assertEqual("model-x", details["llm"])
        self.assertEqual("img:1", details["image"])
        self.assertEqual("1 code snippets", details["extracted"].split(",")[0])


class DockerSoftwaresOfTaskTest(unittest.TestCase):
    def test_collects_the_code_submissions_of_all_teams_with_software(self):
        responses = {
            "/api/count-of-team-software/t": {
                "context": {
                    "count_of_team_software": [
                        {"team": "b", "software_count": 1},
                        {"team": "a", "software_count": 2},
                        {"team": "c", "software_count": 0},
                    ]
                }
            },
            "/api/submissions-for-task/t/a/code": {
                "context": {"code": {"submissions": [{"docker_software_id": 1, "display_name": "s1"}]}}
            },
            "/api/submissions-for-task/t/b/code": {
                "context": {"code": {"submissions": [{"docker_software_id": 2, "display_name": "s2"}]}}
            },
            "/api/submissions-for-task/t/a/docker": {
                "context": {"docker": {"docker_softwares": [{"docker_software_id": 3, "display_name": "s3"}]}}
            },
            "/api/submissions-for-task/t/b/docker": {"context": {"docker": {"docker_softwares": []}}},
        }
        client = MagicMock()
        client.json_response.side_effect = lambda endpoint: responses[endpoint]

        ret = Client.docker_softwares_of_task(client, "t")

        self.assertEqual([("a", "s1"), ("a", "s3"), ("b", "s2")], [(i["team"], i["display_name"]) for i in ret])

    def _credentials_client(self, metadata, featured):
        client = MagicMock()
        client.docker_registry.return_value = "registry"
        client.metadata_for_task.side_effect = lambda task, team: metadata[task]
        client.json_response.return_value = {
            "context": {"task_list": [{"task_id": t, "featured": f} for t, f in featured.items()]}
        }
        client._docker_registry_credentials_of_task.side_effect = lambda t, team: Client._docker_registry_credentials_of_task(
            client, t, team
        )
        return client

    def test_docker_credentials_fall_back_to_first_featured_task(self):
        client = self._credentials_client(
            {
                "t": {"status": 0, "context": {"docker": False}},
                "f1": {"status": 0, "context": {"docker": {"docker_registry_user": "u", "docker_registry_token": "x"}}},
                "f2": {"status": 0, "context": {"docker": {"docker_registry_user": "v", "docker_registry_token": "y"}}},
            },
            {"t": False, "f1": True, "f2": True},
        )

        with self.assertLogs(level="WARNING") as logs:
            ret = Client.docker_credentials(client, "t", "a")

        self.assertEqual(("u", "x", "registry"), ret)
        self.assertIn("featured task f1", logs.output[0])

    def test_docker_credentials_without_featured_task(self):
        client = self._credentials_client({"t": {"status": 0, "context": {"docker": False}}}, {"t": False})

        with self.assertLogs(level="WARNING"):
            ret = Client.docker_credentials(client, "t", "a")

        self.assertEqual((None, None, "registry"), ret)
