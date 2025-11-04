from __future__ import annotations

from uuid import uuid4

import pytest

from algokit_kmd_client.client import KmdClient
from algokit_kmd_client.models import (
    CreateWalletRequest,
    GenerateKeyRequest,
    InitWalletHandleTokenRequest,
    ListKeysRequest,
    ReleaseWalletHandleTokenRequest,
)

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
    assert wallet.id_ is not None
    return wallet.id_, wallet_name


def test_key_management_flow(kmd_client: KmdClient, created_wallet: tuple[str, str]) -> None:
    wallet_id, _ = created_wallet

    init_response = kmd_client.init_wallet_handle_token(
        InitWalletHandleTokenRequest(wallet_id=wallet_id, wallet_password=WALLET_PASSWORD)
    )
    wallet_handle_token = init_response.wallet_handle_token
    assert wallet_handle_token is not None

    try:
        list_before = kmd_client.list_keys_in_wallet(ListKeysRequest(wallet_handle_token=wallet_handle_token))
        before_addresses = list_before.addresses or []

        kmd_client.generate_key(GenerateKeyRequest(wallet_handle_token=wallet_handle_token, display_mnemonic=False))

        list_after = kmd_client.list_keys_in_wallet(ListKeysRequest(wallet_handle_token=wallet_handle_token))
        after_addresses = list_after.addresses or []

        assert len(after_addresses) == len(before_addresses) + 1
    finally:
        kmd_client.release_wallet_handle_token(ReleaseWalletHandleTokenRequest(wallet_handle_token=wallet_handle_token))
