from __future__ import annotations

from uuid import uuid4

import pytest

from algokit_kmd_client.client import KmdClient
from algokit_kmd_client.models import CreateWalletRequest

WALLET_DRIVER = "sqlite"
WALLET_PASSWORD = "testpass"


def _random_wallet_name(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


@pytest.fixture
def created_wallet(kmd_client: KmdClient) -> tuple[str, str]:
    wallet_name = _random_wallet_name("wallet")
    response = kmd_client.create_wallet(
        CreateWalletRequest(
            wallet_name=wallet_name,
            wallet_driver_name=WALLET_DRIVER,
            wallet_password=WALLET_PASSWORD,
        )
    )
    wallet = response.wallet
    assert wallet is not None
    assert wallet.name == wallet_name
    assert wallet.id_ is not None
    return wallet.id_, wallet_name


def test_wallet_lifecycle(kmd_client: KmdClient, created_wallet: tuple[str, str]) -> None:
    _, wallet_name = created_wallet
    list_response = kmd_client.list_wallets()
    wallets = list_response.wallets or []
    assert any(wallet.name == wallet_name for wallet in wallets)
