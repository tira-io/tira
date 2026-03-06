import shutil
import unittest
from pathlib import Path

from tira.rest_api_client import Client
from tira.third_party_integrations import temporary_directory


class TestRestApiNotAvailableTest(unittest.TestCase):

    def clean_tira_cache_dir(self):
        tmp_dir = temporary_directory()
        src_dir = Path(__file__).parent / "resources" / "tira-cache-without-production-system"
        shutil.copy(src_dir / ".tira-settings.json", tmp_dir)

        return tmp_dir

    def test_client_can_be_created(self):
        cache_dir = self.clean_tira_cache_dir()
        tira = Client(tira_cache_dir=Path(cache_dir))
        self.assertIsNotNone(tira)

    def test_all_datasets_works_for_tirex(self):
        cache_dir = self.clean_tira_cache_dir()
        tira = Client(tira_cache_dir=Path(cache_dir))
        actual = tira.datasets("ir-benchmarks")
        self.assertIn("antique-test-20230107-training", actual)

    def test_public_system_details(self):
        cache_dir = self.clean_tira_cache_dir()
        tira = Client(tira_cache_dir=Path(cache_dir))
        actual = tira.public_system_details("tira-ir-starter", "BM25 Re-Rank (tira-ir-starter-pyterrier)")
        self.assertIn("public_image_name", actual)

        self.assertEqual(
            "docker.io/webis/ir-benchmarks-submissions:tira-ir-starter-pyterrier-0-0-1-tira-docker-software-id-plastic-cabin",
            actual["public_image_name"],
        )
