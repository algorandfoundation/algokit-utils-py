import atexit
import os
import socket
import subprocess
import time
from collections.abc import Generator
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path

import pytest
from filelock import FileLock
from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.json import JSONSnapshotExtension

from algokit_algod_client import AlgodClient, ClientConfig
from algokit_indexer_client import ClientConfig as IndexerClientConfig
from algokit_indexer_client import IndexerClient
from algokit_kmd_client import ClientConfig as KmdClientConfig
from algokit_kmd_client import KmdClient
from algokit_utils.algorand import AlgorandClient

# Fixed ports for mock servers - these are consistent across all test workers
# Using high ports to avoid conflicts with common services
MOCK_ALGOD_HOST_PORT = 18000
MOCK_INDEXER_HOST_PORT = 18002
MOCK_KMD_HOST_PORT = 18001

# Internal container ports (what the server listens on inside the container)
MOCK_ALGOD_PORT = 8000
MOCK_INDEXER_PORT = 8002
MOCK_KMD_PORT = 8001

# Default localnet ports (used by algorand_localnet fixture)
LOCALNET_ALGOD_PORT = 4001
LOCALNET_INDEXER_PORT = 8980
LOCALNET_KMD_PORT = 4002

# Default token for both localnet and mock server
DEFAULT_TOKEN = "a" * 64

# Container name prefix for test mock servers
CONTAINER_NAME_PREFIX = "algokit_utils_py_mock"


def _get_mock_server_image() -> str:
    """Get the mock server Docker image name."""
    return os.environ.get("POLYTEST_MOCK_SERVER_IMAGE", "ghcr.io/aorumbayev/polytest-mock-server:latest")


def _get_recordings_path() -> Path:
    """Get the path to the recordings directory."""
    # Check if custom recordings path is set
    custom_path = os.environ.get("POLYTEST_RECORDINGS_PATH")
    if custom_path:
        return Path(custom_path)

    # Default to the algokit-polytest recordings
    return (
        Path(__file__).parent.parent.parent
        / "references"
        / "algokit-polytest"
        / "resources"
        / "mock-server"
        / "recordings"
    )


def _wait_for_port(host: str, port: int, timeout: float = 30.0) -> bool:
    """Wait for a port to become available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect((host, port))
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.1)
    return False


def _is_container_running(container_name: str) -> bool:
    """Check if a container with the given name is already running."""
    result = subprocess.run(
        ["docker", "ps", "-q", "-f", f"name=^{container_name}$"],
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(result.stdout.strip())


def _get_container_id(container_name: str) -> str | None:
    """Get the container ID for a running container by name."""
    result = subprocess.run(
        ["docker", "ps", "-q", "-f", f"name=^{container_name}$"],
        capture_output=True,
        text=True,
        check=False,
    )
    container_id = result.stdout.strip()
    return container_id if container_id else None


# Track all containers started by this process for cleanup (module-level for atexit access)
_started_containers: set[str] = set()

# Flag to track if we're running with pytest-xdist workers
# This is set in _start_or_reuse_mock_server based on environment
_is_xdist_worker: bool = False


def _cleanup_all_containers() -> None:
    """Clean up all containers started by this test session.

    This is called via atexit to ensure containers are cleaned up when the
    test process exits, but only for containers we own.

    When running with pytest-xdist, we skip cleanup in worker processes since
    other workers may still be using the containers. The containers will be
    left running and can be cleaned up manually or by the next test run.
    """
    # Skip cleanup if we're an xdist worker - other workers may still need the containers
    if _is_xdist_worker:
        return

    for container_name in list(_started_containers):
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            check=False,
        )
        _started_containers.discard(container_name)


# Register cleanup at process exit (only happens once per process)
atexit.register(_cleanup_all_containers)


@dataclass
class MockServerContainer:
    """A Docker container running the PollyJS mock server."""

    container_id: str
    container_name: str
    client_type: str
    host_port: int
    container_port: int
    is_owner: bool  # True if this process started the container

    def get_base_url(self) -> str:
        """Get the base URL for the mock server."""
        return f"http://127.0.0.1:{self.host_port}"

    def stop(self) -> None:
        """Stop and remove the container if this process owns it.

        Note: When running with pytest-xdist, cleanup is deferred to atexit
        to avoid race conditions between workers. The container will only
        be stopped when the master process or last worker exits.
        """
        # When running with xdist, we don't stop containers in fixture teardown
        # because other workers may still be using them. The atexit handler
        # will clean them up when the process exits.
        if _is_xdist_worker:
            return

        # Only stop if this process started the container and we're not using xdist
        if self.is_owner and self.container_name in _started_containers:
            subprocess.run(
                ["docker", "rm", "-f", self.container_id],
                capture_output=True,
                check=False,
            )
            _started_containers.discard(self.container_name)


def _start_or_reuse_mock_server(client_type: str, container_port: int, host_port: int) -> MockServerContainer:
    """Start a mock server container or reuse existing one.

    This function is safe to call from multiple pytest-xdist workers. It uses:
    1. File locking to ensure only one process attempts to start a container at a time
    2. Docker container naming to identify existing containers
    """
    global _is_xdist_worker  # noqa: PLW0603

    # Detect if we're running under pytest-xdist
    # xdist sets PYTEST_XDIST_WORKER env var for worker processes (gw0, gw1, etc.)
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    if worker_id is not None:
        _is_xdist_worker = True

    container_name = f"{CONTAINER_NAME_PREFIX}_{client_type}"
    image = _get_mock_server_image()
    recordings_path = _get_recordings_path()
    log_level = os.environ.get("MOCK_SERVER_LOG_LEVEL", "warn")

    # Use FileLock to coordinate container startup between workers
    # This is cross-platform (works on Linux, macOS, Windows)
    lock_file_path = Path(f"/tmp/{container_name}.lock")
    lock = FileLock(lock_file_path)

    with lock:
        # Check if container is already running (now that we have the lock)
        existing_id = _get_container_id(container_name)
        if existing_id:
            # Container already exists, wait for it to be ready and reuse it
            if not _wait_for_port("127.0.0.1", host_port, timeout=30):
                raise TimeoutError(f"Existing mock {client_type} server not responding on port {host_port}")

            return MockServerContainer(
                container_id=existing_id,
                container_name=container_name,
                client_type=client_type,
                host_port=host_port,
                container_port=container_port,
                is_owner=False,  # We didn't start it
            )

        # No container exists, we need to start one
        # First remove any stopped container with same name
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            check=False,
        )

        # Build docker run command
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
            f"LOG_LEVEL={log_level}",
        ]

        # Mount recordings if they exist
        if recordings_path.exists():
            cmd.extend(["-v", f"{recordings_path}:/recordings:ro"])
            cmd.extend([image, client_type, "/recordings"])
        else:
            cmd.extend([image, client_type])

        # Start the container
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            raise RuntimeError(f"Failed to start mock {client_type} server: {result.stderr}")

        container_id = result.stdout.strip()
        _started_containers.add(container_name)

        # Wait for the server to be ready
        if not _wait_for_port("127.0.0.1", host_port, timeout=30):
            # Clean up if startup failed
            subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, check=False)
            _started_containers.discard(container_name)
            raise TimeoutError(f"Mock {client_type} server failed to start within 30 seconds")

        # Additional wait for the server to be fully ready (HAR loading)
        time.sleep(2)

        return MockServerContainer(
            container_id=container_id,
            container_name=container_name,
            client_type=client_type,
            host_port=host_port,
            container_port=container_port,
            is_owner=True,
        )


@pytest.fixture(scope="session")
def mock_algod_server() -> Generator[MockServerContainer, None, None]:
    """
    Start a mock algod server using the PollyJS mock server container.

    This fixture is session-scoped and will start the container once for all tests.
    The mock server replays pre-recorded HAR files for deterministic testing.

    When running with pytest-xdist, multiple workers may try to start the container.
    Only the first one will actually start it; others will reuse the existing container.
    """
    container = _start_or_reuse_mock_server("algod", MOCK_ALGOD_PORT, MOCK_ALGOD_HOST_PORT)
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="session")
def mock_indexer_server() -> Generator[MockServerContainer, None, None]:
    """
    Start a mock indexer server using the PollyJS mock server container.

    This fixture is session-scoped and will start the container once for all tests.
    The mock server replays pre-recorded HAR files for deterministic testing.

    When running with pytest-xdist, multiple workers may try to start the container.
    Only the first one will actually start it; others will reuse the existing container.
    """
    container = _start_or_reuse_mock_server("indexer", MOCK_INDEXER_PORT, MOCK_INDEXER_HOST_PORT)
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="session")
def mock_kmd_server() -> Generator[MockServerContainer, None, None]:
    """
    Start a mock KMD server using the PollyJS mock server container.

    This fixture is session-scoped and will start the container once for all tests.
    The mock server replays pre-recorded HAR files for deterministic testing.

    When running with pytest-xdist, multiple workers may try to start the container.
    Only the first one will actually start it; others will reuse the existing container.
    """
    container = _start_or_reuse_mock_server("kmd", MOCK_KMD_PORT, MOCK_KMD_HOST_PORT)
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture
def algod_client(mock_algod_server: MockServerContainer) -> AlgodClient:
    """
    Create an algod client connected to the mock server.

    The mock server replays pre-recorded responses for deterministic testing.
    """
    config = ClientConfig(
        base_url=mock_algod_server.get_base_url(),
        token=DEFAULT_TOKEN,
    )
    return AlgodClient(config)


@pytest.fixture
def indexer_client(mock_indexer_server: MockServerContainer) -> IndexerClient:
    """
    Create an indexer client connected to the mock server.

    The mock server replays pre-recorded responses for deterministic testing.
    """
    config = IndexerClientConfig(
        base_url=mock_indexer_server.get_base_url(),
        token=DEFAULT_TOKEN,
    )
    return IndexerClient(config)


@pytest.fixture
def kmd_client(mock_kmd_server: MockServerContainer) -> KmdClient:
    """
    Create a KMD client connected to the mock server.

    The mock server replays pre-recorded responses for deterministic testing.
    """
    config = KmdClientConfig(
        base_url=mock_kmd_server.get_base_url(),
        token=DEFAULT_TOKEN,
    )
    return KmdClient(config)


@pytest.fixture
def algorand_localnet() -> AlgorandClient:
    """
    Provide a high-level AlgorandClient configured for localnet.

    Note: This fixture connects to actual localnet, not the mock server.
    Use this only for tests that require real blockchain interaction.
    """
    return AlgorandClient.default_localnet()


# Test configuration constants matching TS mock server config
# These are used for tests that need specific test data from recordings
TEST_ADDRESS = "25M5BT2DMMED3V6CWDEYKSNEFGPXX4QBIINCOICLXXRU3UGTSGRMF3MTOE"
TEST_APP_ID = 718348254
TEST_ASSET_ID = 705457144
TEST_ROUND = 24099447


def _dataclass_to_dict(obj: object) -> object:
    """Recursively convert a dataclass to a dict for JSON serialization.

    Handles nested dataclasses, lists, dicts, bytes, and primitive types.
    """
    if obj is None:
        return None
    if is_dataclass(obj) and not isinstance(obj, type):
        result = {}
        for f in fields(obj):
            value = getattr(obj, f.name)
            result[f.name] = _dataclass_to_dict(value)
        return result
    if isinstance(obj, bytes | bytearray | memoryview):
        return list(bytes(obj))
    if isinstance(obj, list | tuple):
        return [_dataclass_to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    return obj


@pytest.fixture
def snapshot_json(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Snapshot fixture configured for JSON output, suitable for API response testing."""
    return snapshot.with_defaults(extension_class=JSONSnapshotExtension)


class DataclassSnapshotSerializer:
    """Custom serializer that converts dataclass models to JSON-serializable dicts."""

    @staticmethod
    def serialize(data: object) -> object:
        return _dataclass_to_dict(data)
