"""Fixtures for algod client tests using mock server."""

from collections.abc import Generator

import pytest

from algokit_algod_client import AlgodClient, ClientConfig

from tests.modules._mock_server import DEFAULT_TOKEN, MockServer, start_mock_server


@pytest.fixture(scope="session")
def mock_algod_server() -> Generator[MockServer, None, None]:
    """Session-scoped mock algod server for deterministic testing."""
    server = start_mock_server("algod")
    try:
        yield server
    finally:
        server.stop()


@pytest.fixture
def algod_client(mock_algod_server: MockServer) -> AlgodClient:
    """Algod client connected to the mock server."""
    return AlgodClient(ClientConfig(base_url=mock_algod_server.base_url, token=DEFAULT_TOKEN))
