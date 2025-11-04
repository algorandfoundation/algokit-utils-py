import pytest

from algokit_algod_client import AlgodClient, ClientConfig
from algokit_indexer_client import ClientConfig as IndexerClientConfig
from algokit_indexer_client import IndexerClient
from algokit_kmd_client import ClientConfig as KmdClientConfig
from algokit_kmd_client import KmdClient
from algokit_utils.algorand import AlgorandClient


@pytest.fixture
def algod_client() -> AlgodClient:
    """Create an algod client connected to localnet."""
    config = ClientConfig(
        base_url="http://localhost:4001",
        token="a" * 64,
    )
    return AlgodClient(config)


@pytest.fixture
def indexer_client() -> IndexerClient:
    """Create an indexer client connected to localnet."""
    config = IndexerClientConfig(
        base_url="http://localhost:8980",
        token="a" * 64,
    )
    return IndexerClient(config)


@pytest.fixture
def algorand_localnet() -> AlgorandClient:
    """Provide a high-level AlgorandClient configured for localnet."""
    return AlgorandClient.default_localnet()


@pytest.fixture
def kmd_client() -> KmdClient:
    """Create a KMD client connected to localnet."""
    config = KmdClientConfig(
        base_url="http://localhost:4002",
        token="a" * 64,
    )
    return KmdClient(config)
