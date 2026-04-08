"""Fixtures for KMD client tests using localnet."""

from collections.abc import Generator

import pytest

from algokit_algod_client import AlgodClient
from algokit_algod_client import ClientConfig as AlgodClientConfig
from algokit_kmd_client import ClientConfig, KmdClient

from .fixtures import (
    get_wallet_handle,
    release_wallet_handle,
)

# Localnet configuration
LOCALNET_KMD_TOKEN = "a" * 64
LOCALNET_KMD_URL = "http://localhost:4002"
LOCALNET_ALGOD_TOKEN = "a" * 64
LOCALNET_ALGOD_URL = "http://localhost:4001"


@pytest.fixture
def localnet_kmd_client() -> KmdClient:
    """KMD client connected to localnet."""
    return KmdClient(ClientConfig(base_url=LOCALNET_KMD_URL, token=LOCALNET_KMD_TOKEN))


@pytest.fixture
def localnet_algod_client() -> AlgodClient:
    """Algod client connected to localnet."""
    return AlgodClient(AlgodClientConfig(base_url=LOCALNET_ALGOD_URL, token=LOCALNET_ALGOD_TOKEN))


@pytest.fixture
def wallet_handle(localnet_kmd_client: KmdClient) -> Generator[tuple[str, str, str], None, None]:
    """Creates a wallet and provides a wallet handle token.

    Yields (wallet_handle_token, wallet_id, wallet_name).
    Automatically releases the handle after the test.
    """
    wallet_handle_token, wallet_id, wallet_name = get_wallet_handle(localnet_kmd_client)
    try:
        yield wallet_handle_token, wallet_id, wallet_name
    finally:
        release_wallet_handle(localnet_kmd_client, wallet_handle_token)
