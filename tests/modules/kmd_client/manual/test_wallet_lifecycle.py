from uuid import uuid4

import pytest

from algokit_kmd_client import ClientConfig, KmdClient
from algokit_kmd_client.models import CreateWalletRequest

WALLET_PASSWORD = "testpass"


def _random_wallet_name(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


@pytest.fixture
def localnet_kmd_client() -> KmdClient:
    """Create a KMD client connected to localnet."""
    config = ClientConfig(
        base_url="http://localhost:4002",
        token="a" * 64,
    )
    return KmdClient(config)


@pytest.fixture
def created_wallet(localnet_kmd_client: KmdClient) -> tuple[str, str]:
    wallet_name = _random_wallet_name("wallet")
    response = localnet_kmd_client.create_wallet(
        CreateWalletRequest(
            wallet_name=wallet_name,
            wallet_password=WALLET_PASSWORD,
        )
    )
    wallet = response.wallet
    assert wallet is not None
    assert wallet.name == wallet_name
    assert wallet.id_ is not None
    return wallet.id_, wallet_name


@pytest.mark.localnet
def test_wallet_lifecycle(localnet_kmd_client: KmdClient, created_wallet: tuple[str, str]) -> None:
    """Test KMD wallet lifecycle using localnet.

    NOTE: This test requires localnet to be running with KMD.
    """
    _, wallet_name = created_wallet
    list_response = localnet_kmd_client.list_wallets()
    wallets = list_response.wallets or []
    assert any(wallet.name == wallet_name for wallet in wallets)
