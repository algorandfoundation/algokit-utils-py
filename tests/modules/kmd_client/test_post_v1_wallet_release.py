import pytest

from algokit_kmd_client import KmdClient
from algokit_kmd_client.exceptions import UnexpectedStatusError
from algokit_kmd_client.models import ReleaseWalletHandleTokenRequest, WalletInfoRequest

from .fixtures import get_wallet_handle

# Polytest Suite: POST v1_wallet_release

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
@pytest.mark.localnet
def test_basic_request_and_response_validation(localnet_kmd_client: KmdClient) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    # Create our own wallet handle since we need to release it (not use the fixture)
    wallet_handle_token, _, _ = get_wallet_handle(localnet_kmd_client)

    # Release should succeed (returns empty response)
    localnet_kmd_client.release_wallet_handle_token(
        ReleaseWalletHandleTokenRequest(wallet_handle_token=wallet_handle_token)
    )

    # Verify the handle is now invalid by trying to use it
    with pytest.raises(UnexpectedStatusError, match="handle does not exist"):
        localnet_kmd_client.wallet_info(WalletInfoRequest(wallet_handle_token=wallet_handle_token))
