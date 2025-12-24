import pytest

from algokit_kmd_client import KmdClient
from algokit_kmd_client.models import InitWalletHandleTokenRequest

from .fixtures import TEST_WALLET_PASSWORD, create_test_wallet

# Polytest Suite: POST v1_wallet_init

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
@pytest.mark.localnet
def test_basic_request_and_response_validation(localnet_kmd_client: KmdClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    # Create a wallet first
    wallet_id, _ = create_test_wallet(localnet_kmd_client)

    result = localnet_kmd_client.init_wallet_handle(
        InitWalletHandleTokenRequest(
            wallet_id=wallet_id,
            wallet_password=TEST_WALLET_PASSWORD,
        )
    )

    assert result.wallet_handle_token is not None
