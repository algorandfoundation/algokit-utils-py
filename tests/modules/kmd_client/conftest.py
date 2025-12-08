"""Fixtures for KMD client tests using mock server."""

import pytest

from algokit_kmd_client import ClientConfig, KmdClient

from tests.modules._mock_server import DEFAULT_TOKEN, MockServer, get_mock_server


@pytest.fixture(scope="session")
def mock_kmd_server() -> MockServer:
    """Session-scoped mock KMD server for deterministic testing."""
    return get_mock_server("kmd")


@pytest.fixture
def kmd_client(mock_kmd_server: MockServer) -> KmdClient:
    """KMD client connected to the mock server."""
    return KmdClient(ClientConfig(base_url=mock_kmd_server.base_url, token=DEFAULT_TOKEN))
