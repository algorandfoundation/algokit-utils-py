import pytest

from algokit_kmd_client import KmdClient

from .fixtures import create_test_wallet

# Polytest Suite: POST v1_wallet

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
@pytest.mark.localnet
def test_basic_request_and_response_validation(localnet_kmd_client: KmdClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    wallet_id, wallet_name = create_test_wallet(localnet_kmd_client)

    # Verify the wallet was created
    list_result = localnet_kmd_client.list_wallets()
    wallets = list_result.wallets or []
    created_wallet = next((w for w in wallets if w.id_ == wallet_id), None)
    assert created_wallet is not None
    assert created_wallet.name == wallet_name
