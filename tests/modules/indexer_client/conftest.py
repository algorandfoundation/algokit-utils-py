"""Fixtures for indexer client tests using mock server."""

import pytest

from algokit_indexer_client import ClientConfig, IndexerClient

from tests.modules._mock_server import DEFAULT_TOKEN, MockServer, get_mock_server


@pytest.fixture(scope="session")
def mock_indexer_server() -> MockServer:
    """Session-scoped mock indexer server for deterministic testing."""
    return get_mock_server("indexer")


@pytest.fixture
def indexer_client(mock_indexer_server: MockServer) -> IndexerClient:
    """Indexer client connected to the mock server."""
    return IndexerClient(ClientConfig(base_url=mock_indexer_server.base_url, token=DEFAULT_TOKEN))
