import pytest

from algokit_kmd_client import KmdClient
from algokit_kmd_client.models import ListKeysRequest

from .fixtures import generate_test_key

# Polytest Suite: POST v1_key_list

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
@pytest.mark.localnet
def test_basic_request_and_response_validation(
    localnet_kmd_client: KmdClient,
    wallet_handle: tuple[str, str, str],
) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    wallet_handle_token, _, _ = wallet_handle

    # Generate at least one key
    generate_test_key(localnet_kmd_client, wallet_handle_token)

    result = localnet_kmd_client.list_keys_in_wallet(
        ListKeysRequest(wallet_handle_token=wallet_handle_token)
    )

    assert result.addresses is not None
    assert len(result.addresses) > 0
