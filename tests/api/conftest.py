import pytest
from algod_client import AlgodClient, ClientConfig


@pytest.fixture
def algod_client() -> AlgodClient:
    """Create an algod client connected to localnet."""
    config = ClientConfig(
        base_url="http://localhost:4001",
        token="a" * 64,
    )
    return AlgodClient(config)
