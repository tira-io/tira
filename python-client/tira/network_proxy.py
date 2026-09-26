"""Helpers to restrict the network access of a sandboxed execution container to a configurable list
of hostnames instead of granting it unrestricted network access.

The approach is: start a small forward-proxy container (see ./docker/network-proxy) that only allows
HTTP(S) traffic to an explicit allowlist of hostnames, connect it to both the normal (internet-facing)
docker network and a freshly created, isolated ("internal") docker network, and then attach the
sandboxed execution container only to that isolated network. The sandboxed container therefore has no
direct route to the internet at all; it can only reach the allowed hostnames by using the proxy
(exposed as http(s)_proxy environment variables), which is the only container that is reachable to it.
"""

import logging
import re
import uuid
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional

if TYPE_CHECKING:
    from docker import DockerClient
    from docker.models.containers import Container
    from docker.models.networks import Network

PROXY_IMAGE = "ghcr.io/tira-io/tira-proxy:0.0.1"
PROXY_ALIAS = "tira-network-proxy"
PROXY_PORT = 8888
EXTERNAL_NETWORK = "bridge"

# Matches the tinyproxy log line that is written whenever the proxy establishes a connection to an
# allowed host on behalf of a client, e.g.:
#   CONNECT   Aug 27 17:02:54.362 [1]: Established connection to host "example.com" using file
#   descriptor 5.
_ACCESSED_HOSTNAME_PATTERN = re.compile(r'Established connection to host "([^"]+)"')

# Matches the tinyproxy log line that is written whenever the proxy refuses a connection to a host that
# is not on the allowlist, e.g.:
#   NOTICE    Aug 27 17:02:54.850 [1]: Proxying refused on filtered domain "denied.example.com"
_BLOCKED_HOSTNAME_PATTERN = re.compile(r'Proxying refused on filtered domain "([^"]+)"')


class NetworkProxy:
    """A running proxy container plus the isolated docker network that connects it to a sandboxed
    execution container."""

    def __init__(
        self,
        client: "DockerClient",
        network: "Network",
        container: "Container",
        allowed_hostnames: "List[str]",
        access_log_file: "Optional[Path]" = None,
    ):
        self.client = client
        self.network = network
        self.container = container
        self.allowed_hostnames = allowed_hostnames
        self.access_log_file = access_log_file

    @property
    def environment_variables(self) -> "dict":
        """Environment variables to add to the sandboxed execution container so that well-behaved
        HTTP(S) clients (requests, curl, wget, ...) route their traffic through this proxy."""
        proxy_url = f"http://{PROXY_ALIAS}:{PROXY_PORT}"
        no_proxy = "localhost,127.0.0.1"
        return {
            "http_proxy": proxy_url,
            "https_proxy": proxy_url,
            "HTTP_PROXY": proxy_url,
            "HTTPS_PROXY": proxy_url,
            "no_proxy": no_proxy,
            "NO_PROXY": no_proxy,
        }

    def accessed_hostname_counts(self) -> "Dict[str, int]":
        """Returns a mapping of hostname to the number of requests the proxy actually granted access
        to that hostname (i.e., that were successfully connected to), extracted from the proxy
        container's log."""
        try:
            raw_log = self.container.logs().decode("utf-8", errors="replace")
            return dict(Counter(_ACCESSED_HOSTNAME_PATTERN.findall(raw_log)))
        except Exception:
            logging.debug("Could not read the log of the network proxy container.", exc_info=True)
            return {}

    def blocked_hostname_counts(self) -> "Dict[str, int]":
        """Returns a mapping of hostname to the number of requests the proxy refused (i.e., that were
        not on the allowlist), extracted from the proxy container's log."""
        try:
            raw_log = self.container.logs().decode("utf-8", errors="replace")
            return dict(Counter(_BLOCKED_HOSTNAME_PATTERN.findall(raw_log)))
        except Exception:
            logging.debug("Could not read the log of the network proxy container.", exc_info=True)
            return {}

    def write_access_log(self) -> None:
        """Persists the number of requests per hostname the proxy granted or refused access to at
        'self.access_log_file', if set. Each line contains the hostname, whether the requests were
        allowed or blocked, and the request count, e.g. 'example.com\\tALLOW\\t3\\n'."""
        if not self.access_log_file:
            return

        allowed_counts = self.accessed_hostname_counts()
        blocked_counts = self.blocked_hostname_counts()
        try:
            self.access_log_file.parent.mkdir(parents=True, exist_ok=True)
            lines = [f"{hostname}\tALLOW\t{count}\n" for hostname, count in sorted(allowed_counts.items())]
            lines += [f"{hostname}\tBLOCK\t{count}\n" for hostname, count in sorted(blocked_counts.items())]
            self.access_log_file.write_text("".join(lines))
        except Exception:
            logging.debug(f"Could not write the network access log to {self.access_log_file}.", exc_info=True)

    def stop(self) -> None:
        self.write_access_log()

        try:
            self.container.remove(force=True)
        except Exception:
            logging.debug("Could not remove the network proxy container.", exc_info=True)

        try:
            self.network.remove()
        except Exception:
            logging.debug("Could not remove the isolated network of the network proxy.", exc_info=True)


def ensure_proxy_image_available(client: "DockerClient", image: str = PROXY_IMAGE) -> None:
    try:
        client.images.get(image)
        return
    except Exception:
        pass

    logging.info(f"Pulling the network proxy image {image} ...")
    client.images.pull(image)


def start_network_proxy(
    client: "DockerClient",
    allowed_hostnames: "Iterable[str]",
    image: str = PROXY_IMAGE,
    access_log_file: "Optional[Path]" = None,
) -> NetworkProxy:
    """Starts a proxy container that only allows outgoing HTTP(S) traffic to 'allowed_hostnames' and
    connects it to a freshly created, isolated docker network.

    Attach the sandboxed execution container only to 'NetworkProxy.network' (and add
    'NetworkProxy.environment_variables' to its environment) so that it can only reach the internet
    through the whitelisted hostnames. If 'access_log_file' is set, the number of requests per hostname
    the proxy granted or refused access to are written there (one "hostname\\tALLOW|BLOCK\\tcount"
    triple per line) when the proxy is stopped.
    """
    allowed_hostnames = sorted({h.strip() for h in allowed_hostnames if h and h.strip()})
    if not allowed_hostnames:
        raise ValueError("allowed_hostnames must not be empty.")

    ensure_proxy_image_available(client, image)

    network_name = f"tira-network-proxy-{uuid.uuid4().hex[:12]}"
    network = client.networks.create(network_name, driver="bridge", internal=True)

    try:
        container = client.containers.run(
            image,
            environment={"TIRA_ALLOWED_HOSTNAMES": ",".join(allowed_hostnames)},
            network=EXTERNAL_NETWORK,
            detach=True,
            remove=True,
        )
    except Exception:
        network.remove()
        raise

    try:
        network.connect(container, aliases=[PROXY_ALIAS])
    except Exception:
        try:
            container.remove(force=True)
        finally:
            network.remove()
        raise

    return NetworkProxy(client, network, container, allowed_hostnames, access_log_file)
