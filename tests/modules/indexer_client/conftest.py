"""Fixtures for indexer client tests using mock server."""

from collections.abc import Generator

import pytest

from algokit_indexer_client import ClientConfig, IndexerClient

from tests.modules._mock_server import DEFAULT_TOKEN, MockServer, start_mock_server


@pytest.fixture(scope="session")
def mock_indexer_server() -> Generator[MockServer, None, None]:
    """Session-scoped mock indexer server for deterministic testing."""
    server = start_mock_server("indexer")
    try:
        yield server
    finally:
        server.stop()


@pytest.fixture
def indexer_client(mock_indexer_server: MockServer) -> IndexerClient:
    """Indexer client connected to the mock server."""
    return IndexerClient(ClientConfig(base_url=mock_indexer_server.base_url, token=DEFAULT_TOKEN))
