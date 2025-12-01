from uuid import uuid4

import pytest

from algokit_kmd_client import ClientConfig, KmdClient
from algokit_kmd_client.models import (
    CreateWalletRequest,
    GenerateKeyRequest,
    InitWalletHandleTokenRequest,
    ListKeysRequest,
    ReleaseWalletHandleTokenRequest,
)

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
    assert wallet.id_ is not None
    return wallet.id_, wallet_name


@pytest.mark.localnet
def test_key_management_flow(localnet_kmd_client: KmdClient, created_wallet: tuple[str, str]) -> None:
    """Test KMD key management using localnet.

    NOTE: This test requires localnet to be running with KMD.
    """
    wallet_id, _ = created_wallet

    init_response = localnet_kmd_client.init_wallet_handle_token(
        InitWalletHandleTokenRequest(wallet_id=wallet_id, wallet_password=WALLET_PASSWORD)
    )
    wallet_handle_token = init_response.wallet_handle_token
    assert wallet_handle_token is not None

    try:
        list_before = localnet_kmd_client.list_keys_in_wallet(ListKeysRequest(wallet_handle_token=wallet_handle_token))
        before_addresses = list_before.addresses or []

        localnet_kmd_client.generate_key(
            GenerateKeyRequest(wallet_handle_token=wallet_handle_token, display_mnemonic=False)
        )

        list_after = localnet_kmd_client.list_keys_in_wallet(ListKeysRequest(wallet_handle_token=wallet_handle_token))
        after_addresses = list_after.addresses or []

        assert len(after_addresses) == len(before_addresses) + 1
    finally:
        localnet_kmd_client.release_wallet_handle_token(
            ReleaseWalletHandleTokenRequest(wallet_handle_token=wallet_handle_token)
        )
