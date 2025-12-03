"""Mock server infrastructure for algod/indexer/kmd client testing.

This module provides Docker-based mock servers that replay pre-recorded HAR files
for deterministic API testing. Only used by algod_client, indexer_client, and
kmd_client test modules.

Environment Variables:
    MOCK_ALGOD_URL: External algod mock server URL (e.g., http://localhost:18000)
    MOCK_INDEXER_URL: External indexer mock server URL (e.g., http://localhost:18002)
    MOCK_KMD_URL: External KMD mock server URL (e.g., http://localhost:18001)

    When set, tests will use the external server instead of spinning up Docker.
    The server must be running and pass a health check.
"""

from __future__ import annotations

import atexit
import os
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# Port configuration
MOCK_PORTS = {
    "algod": {"host": 18000, "container": 8000},
    "indexer": {"host": 18002, "container": 8002},
    "kmd": {"host": 18001, "container": 8001},
}

# Environment variable names for external server URLs
EXTERNAL_URL_ENV_VARS = {
    "algod": "MOCK_ALGOD_URL",
    "indexer": "MOCK_INDEXER_URL",
    "kmd": "MOCK_KMD_URL",
}

DEFAULT_TOKEN = "a" * 64
CONTAINER_PREFIX = "algokit_utils_py_mock"

# Track containers for cleanup
_started_containers: set[str] = set()
_is_xdist_worker = False


def _cleanup_containers() -> None:
    """Clean up containers on exit (skipped for xdist workers)."""
    if _is_xdist_worker:
        return
    for name in list(_started_containers):
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, check=False)
        _started_containers.discard(name)


atexit.register(_cleanup_containers)


@dataclass
class MockServer:
    """A running mock server container."""

    container_id: str
    name: str
    client_type: str
    port: int
    is_owner: bool

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def stop(self) -> None:
        """Stop container if owned and not running under xdist."""
        if _is_xdist_worker or not self.is_owner:
            return
        if self.name in _started_containers:
            subprocess.run(["docker", "rm", "-f", self.container_id], capture_output=True, check=False)
            _started_containers.discard(self.name)


def _wait_for_port(port: int, timeout: float = 30.0) -> bool:
    """Wait for a port to become available."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect(("127.0.0.1", port))
                return True
        except OSError:
            time.sleep(0.1)
    return False


def _wait_for_health(port: int, timeout: float = 30.0) -> bool:
    """Wait for the mock server to respond to HTTP requests.

    The mock server uses Fastify with a catch-all route, so any request
    should work. We use the /health path by convention, but any path would
    respond (possibly with a 404/500 from HAR replay, which still indicates readiness).
    """
    start = time.time()
    url = f"http://127.0.0.1:{port}/health"
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2) as response:
                # Any response (even error) means server is ready
                _ = response.read()
                return True
        except urllib.error.HTTPError:
            # HTTP error responses (4xx, 5xx) still indicate server is ready
            return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.2)
    return False


def _get_container_id(name: str) -> str | None:
    """Get container ID if running."""
    result = subprocess.run(
        ["docker", "ps", "-q", "-f", f"name=^{name}$"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or None


def _get_image() -> str:
    return os.environ.get("POLYTEST_MOCK_SERVER_IMAGE", "ghcr.io/aorumbayev/polytest-mock-server:latest")


def _get_recordings_path() -> Path:
    if custom := os.environ.get("POLYTEST_RECORDINGS_PATH"):
        return Path(custom)
    return Path(__file__).parent.parent / "references" / "algokit-polytest" / "resources" / "mock-server" / "recordings"


def _get_external_server_url(client_type: str) -> str | None:
    """Get external server URL from environment if configured."""
    env_var = EXTERNAL_URL_ENV_VARS.get(client_type)
    return os.environ.get(env_var) if env_var else None


def _check_external_server(url: str, timeout: float = 5.0) -> tuple[bool, int]:
    """Check if external server is healthy. Returns (is_healthy, port)."""
    parsed = urllib.parse.urlparse(url)
    port = parsed.port or 80
    health_url = f"{url.rstrip('/')}/health"

    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(health_url, method="GET")
            with urllib.request.urlopen(req, timeout=2):
                return True, port
        except urllib.error.HTTPError:
            # HTTP error responses still indicate server is ready
            return True, port
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.2)
    return False, port


def start_mock_server(client_type: str) -> MockServer:
    """Start or connect to a mock server for the given client type.

    Priority:
        1. External server via MOCK_ALGOD_URL / MOCK_INDEXER_URL / MOCK_KMD_URL
        2. Existing Docker container
        3. New Docker container

    Thread-safe across pytest-xdist workers via file locking.
    """
    global _is_xdist_worker  # noqa: PLW0603

    if os.environ.get("PYTEST_XDIST_WORKER"):
        _is_xdist_worker = True

    # Check for external server URL
    if external_url := _get_external_server_url(client_type):
        is_healthy, port = _check_external_server(external_url)
        if is_healthy:
            return MockServer("external", "external", client_type, port, is_owner=False)
        env_var = EXTERNAL_URL_ENV_VARS[client_type]
        raise RuntimeError(
            f"{env_var}={external_url} is set but server health check failed. "
            f"Ensure the mock server is running at {external_url}"
        )

    ports = MOCK_PORTS[client_type]
    host_port, container_port = ports["host"], ports["container"]
    container_name = f"{CONTAINER_PREFIX}_{client_type}"

    # Use file lock for xdist coordination
    from filelock import FileLock

    lock_path = Path(tempfile.gettempdir()) / f"{container_name}.lock"
    with FileLock(str(lock_path)):
        # Reuse existing container
        if existing_id := _get_container_id(container_name):
            if not _wait_for_port(host_port):
                raise TimeoutError(f"Existing {client_type} server not responding on port {host_port}")
            return MockServer(existing_id, container_name, client_type, host_port, is_owner=False)

        # Remove any stopped container
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, check=False)

        # Build command
        cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "-p",
            f"{host_port}:{container_port}",
            "-e",
            f"{client_type.upper()}_PORT={container_port}",
            "-e",
            f"LOG_LEVEL={os.environ.get('MOCK_SERVER_LOG_LEVEL', 'warn')}",
        ]

        recordings = _get_recordings_path()
        image = _get_image()
        if recordings.exists():
            cmd.extend(["-v", f"{recordings}:/recordings:ro", image, client_type, "/recordings"])
        else:
            cmd.extend([image, client_type])

        # Start container
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to start {client_type} mock server: {result.stderr}")

        container_id = result.stdout.strip()
        _started_containers.add(container_name)

        if not _wait_for_port(host_port):
            subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, check=False)
            _started_containers.discard(container_name)
            raise TimeoutError(f"{client_type} mock server failed to start")

        # Wait for server to be fully ready (HAR loading complete)
        if not _wait_for_health(host_port, timeout=30.0):
            subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, check=False)
            _started_containers.discard(container_name)
            raise TimeoutError(f"{client_type} mock server health check failed")

        return MockServer(container_id, container_name, client_type, host_port, is_owner=True)
