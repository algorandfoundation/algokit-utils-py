import pytest

from algokit_kmd_client import KmdClient
from algokit_kmd_client.models import RenameWalletRequest, WalletInfoRequest

from .fixtures import TEST_WALLET_PASSWORD

# Polytest Suite: POST v1_wallet_rename

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
@pytest.mark.localnet
def test_basic_request_and_response_validation(
    localnet_kmd_client: KmdClient,
    wallet_handle: tuple[str, str, str],
) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    wallet_handle_token, wallet_id, wallet_name = wallet_handle

    new_wallet_name = f"{wallet_name}-renamed"
    result = localnet_kmd_client.rename_wallet(
        RenameWalletRequest(
            wallet_id=wallet_id,
            wallet_password=TEST_WALLET_PASSWORD,
            wallet_name=new_wallet_name,
        )
    )

    assert result.wallet is not None

    # Verify the wallet was renamed
    wallet_info = localnet_kmd_client.wallet_info(
        WalletInfoRequest(wallet_handle_token=wallet_handle_token)
    )
    assert wallet_info.wallet_handle is not None
    assert wallet_info.wallet_handle.wallet is not None
    assert wallet_info.wallet_handle.wallet.name == new_wallet_name
