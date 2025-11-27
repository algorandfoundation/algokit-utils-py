import os
from collections.abc import Generator
from pathlib import Path

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from algokit_algod_client import AlgodClient, ClientConfig
from algokit_indexer_client import ClientConfig as IndexerClientConfig
from algokit_indexer_client import IndexerClient
from algokit_kmd_client import ClientConfig as KmdClientConfig
from algokit_kmd_client import KmdClient
from algokit_utils.algorand import AlgorandClient

# Default ports for mock server
MOCK_ALGOD_PORT = 8000
MOCK_INDEXER_PORT = 8002
MOCK_KMD_PORT = 8001

# Default localnet ports (used by algorand_localnet fixture)
LOCALNET_ALGOD_PORT = 4001
LOCALNET_INDEXER_PORT = 8980
LOCALNET_KMD_PORT = 4002

# Default token for both localnet and mock server
DEFAULT_TOKEN = "a" * 64


def _get_mock_server_image() -> str:
    """Get the mock server Docker image name."""
    # TODO: Update to algorandfoundation/polytest-mock-server:latest once published to DockerHub
    return os.environ.get("POLYTEST_MOCK_SERVER_IMAGE", "polytest-mock-server:local")


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


class MockServerContainer(DockerContainer):
    """A Docker container running the PollyJS mock server."""

    def __init__(self, client_type: str, port: int, recordings_path: Path | None = None) -> None:
        image = _get_mock_server_image()
        super().__init__(image)

        self.client_type = client_type
        self.port = port
        self.recordings_path = recordings_path or _get_recordings_path()

        # Configure the container
        self.with_exposed_ports(port)
        self.with_command(client_type)

        # Mount recordings if they exist
        if self.recordings_path.exists():
            self.with_volume_mapping(str(self.recordings_path), "/recordings", mode="ro")
            self.with_command(f"{client_type} /recordings")

        # Set environment variables
        self.with_env(f"{client_type.upper()}_PORT", str(port))
        self.with_env("LOG_LEVEL", os.environ.get("MOCK_SERVER_LOG_LEVEL", "warn"))

    def get_base_url(self) -> str:
        """Get the base URL for the mock server."""
        host = self.get_container_host_ip()
        mapped_port = self.get_exposed_port(self.port)
        return f"http://{host}:{mapped_port}"


@pytest.fixture(scope="session")
def mock_algod_server() -> Generator[MockServerContainer, None, None]:
    """
    Start a mock algod server using the PollyJS mock server container.

    This fixture is session-scoped and will start the container once for all tests.
    The mock server replays pre-recorded HAR files for deterministic testing.
    """
    container = MockServerContainer("algod", MOCK_ALGOD_PORT)
    try:
        container.start()
        # Wait for server to be ready
        wait_for_logs(container, "Server listening on port", timeout=30)
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="session")
def mock_indexer_server() -> Generator[MockServerContainer, None, None]:
    """
    Start a mock indexer server using the PollyJS mock server container.

    This fixture is session-scoped and will start the container once for all tests.
    The mock server replays pre-recorded HAR files for deterministic testing.
    """
    container = MockServerContainer("indexer", MOCK_INDEXER_PORT)
    try:
        container.start()
        # Wait for server to be ready
        wait_for_logs(container, "Server listening on port", timeout=30)
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="session")
def mock_kmd_server() -> Generator[MockServerContainer, None, None]:
    """
    Start a mock KMD server using the PollyJS mock server container.

    This fixture is session-scoped and will start the container once for all tests.
    The mock server replays pre-recorded HAR files for deterministic testing.
    """
    container = MockServerContainer("kmd", MOCK_KMD_PORT)
    try:
        container.start()
        # Wait for server to be ready
        wait_for_logs(container, "Server listening on port", timeout=30)
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
