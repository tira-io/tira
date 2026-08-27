import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from tira.network_proxy import EXTERNAL_NETWORK, PROXY_ALIAS, PROXY_IMAGE, start_network_proxy


class TestNetworkProxy(unittest.TestCase):
    def test_start_network_proxy_raises_for_empty_allowlist(self):
        client = MagicMock()

        with self.assertRaises(ValueError):
            start_network_proxy(client, [])

    def test_start_network_proxy_creates_an_internal_network(self):
        client = MagicMock()
        client.images.get.return_value = MagicMock()

        start_network_proxy(client, ["api.openai.com"])

        self.assertEqual(client.networks.create.call_count, 1)
        _, kwargs = client.networks.create.call_args
        self.assertEqual(kwargs.get("internal"), True)

    def test_start_network_proxy_pulls_the_image_if_missing(self):
        client = MagicMock()
        client.images.get.side_effect = Exception("not found")

        start_network_proxy(client, ["api.openai.com"])

        client.images.pull.assert_called_once_with(PROXY_IMAGE)

    def test_start_network_proxy_does_not_repull_existing_image(self):
        client = MagicMock()
        client.images.get.return_value = MagicMock()

        start_network_proxy(client, ["api.openai.com"])

        client.images.pull.assert_not_called()

    def test_start_network_proxy_passes_allowed_hostnames_to_the_container(self):
        client = MagicMock()
        client.images.get.return_value = MagicMock()

        start_network_proxy(client, ["api.openai.com", "orbit.example.com "])

        _, kwargs = client.containers.run.call_args
        self.assertEqual(kwargs["environment"]["TIRA_ALLOWED_HOSTNAMES"], "api.openai.com,orbit.example.com")
        self.assertEqual(kwargs["network"], EXTERNAL_NETWORK)

    def test_start_network_proxy_connects_container_to_the_isolated_network_with_alias(self):
        client = MagicMock()
        client.images.get.return_value = MagicMock()
        network = MagicMock()
        client.networks.create.return_value = network
        container = MagicMock()
        client.containers.run.return_value = container

        proxy = start_network_proxy(client, ["api.openai.com"])

        network.connect.assert_called_once_with(container, aliases=[PROXY_ALIAS])
        self.assertIs(proxy.network, network)
        self.assertIs(proxy.container, container)

    def test_environment_variables_point_to_the_proxy_alias(self):
        client = MagicMock()
        client.images.get.return_value = MagicMock()

        proxy = start_network_proxy(client, ["api.openai.com"])
        env = proxy.environment_variables

        self.assertEqual(env["http_proxy"], f"http://{PROXY_ALIAS}:8888")
        self.assertEqual(env["https_proxy"], f"http://{PROXY_ALIAS}:8888")

    def test_stop_removes_container_and_network(self):
        client = MagicMock()
        client.images.get.return_value = MagicMock()
        network = MagicMock()
        client.networks.create.return_value = network
        container = MagicMock()
        client.containers.run.return_value = container

        proxy = start_network_proxy(client, ["api.openai.com"])
        proxy.stop()

        container.remove.assert_called_once_with(force=True)
        network.remove.assert_called_once()

    def test_stop_is_robust_against_errors(self):
        client = MagicMock()
        client.images.get.return_value = MagicMock()
        network = MagicMock()
        client.networks.create.return_value = network
        container = MagicMock()
        container.remove.side_effect = Exception("boom")
        client.containers.run.return_value = container

        proxy = start_network_proxy(client, ["api.openai.com"])
        proxy.stop()  # should not raise

        network.remove.assert_called_once()

    def test_start_network_proxy_removes_network_if_container_start_fails(self):
        client = MagicMock()
        client.images.get.return_value = MagicMock()
        network = MagicMock()
        client.networks.create.return_value = network
        client.containers.run.side_effect = Exception("boom")

        with self.assertRaises(Exception):
            start_network_proxy(client, ["api.openai.com"])

        network.remove.assert_called_once()

    def test_accessed_hostname_counts_counts_requests_per_host(self):
        client = MagicMock()
        client.images.get.return_value = MagicMock()
        container = MagicMock()
        container.logs.return_value = (
            b'CONNECT   Aug 27 17:02:53.876 [1]: Established connection to host "example.com" using'
            b" file descriptor 5.\n"
            b'CONNECT   Aug 27 17:02:54.362 [1]: Established connection to host "example.com" using'
            b" file descriptor 5.\n"
            b'CONNECT   Aug 27 17:02:55.000 [1]: Established connection to host "api.openai.com" using'
            b" file descriptor 6.\n"
            b'NOTICE    Aug 27 17:02:54.850 [1]: Proxying refused on filtered domain "denied.example.com"\n'
        )
        client.containers.run.return_value = container

        proxy = start_network_proxy(client, ["example.com", "api.openai.com", "denied.example.com"])

        self.assertEqual(proxy.accessed_hostname_counts(), {"example.com": 2, "api.openai.com": 1})

    def test_accessed_hostname_counts_is_robust_against_errors(self):
        client = MagicMock()
        client.images.get.return_value = MagicMock()
        container = MagicMock()
        container.logs.side_effect = Exception("boom")
        client.containers.run.return_value = container

        proxy = start_network_proxy(client, ["api.openai.com"])

        self.assertEqual(proxy.accessed_hostname_counts(), {})

    def test_write_access_log_persists_request_counts_per_host_next_to_output(self):
        client = MagicMock()
        client.images.get.return_value = MagicMock()
        container = MagicMock()
        container.logs.return_value = (
            b'CONNECT [1]: Established connection to host "example.com" using file descriptor 5.\n'
            b'CONNECT [1]: Established connection to host "example.com" using file descriptor 5.\n'
            b'CONNECT [1]: Established connection to host "api.openai.com" using file descriptor 6.\n'
        )
        client.containers.run.return_value = container

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "output"
            output_dir.mkdir()
            access_log_file = output_dir.parent / "network-access.log"

            proxy = start_network_proxy(client, ["example.com", "api.openai.com"], access_log_file=access_log_file)
            proxy.write_access_log()

            self.assertEqual(access_log_file.read_text(), "api.openai.com\t1\nexample.com\t2\n")

    def test_stop_writes_access_log_before_removing_the_container(self):
        client = MagicMock()
        client.images.get.return_value = MagicMock()
        container = MagicMock()
        container.logs.return_value = (
            b'CONNECT [1]: Established connection to host "example.com" using file descriptor 5.\n'
        )
        client.containers.run.return_value = container

        with tempfile.TemporaryDirectory() as tmp_dir:
            access_log_file = Path(tmp_dir) / "network-access.log"

            proxy = start_network_proxy(client, ["example.com"], access_log_file=access_log_file)
            proxy.stop()

            self.assertEqual(access_log_file.read_text(), "example.com\t1\n")
            container.remove.assert_called_once_with(force=True)

    def test_write_access_log_does_nothing_without_a_configured_path(self):
        client = MagicMock()
        client.images.get.return_value = MagicMock()

        proxy = start_network_proxy(client, ["api.openai.com"])
        proxy.write_access_log()  # should not raise
