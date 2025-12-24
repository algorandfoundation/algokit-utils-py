import pytest

from algokit_kmd_client import KmdClient
from algokit_kmd_client.models import DeleteKeyRequest, ListKeysRequest

from .fixtures import TEST_WALLET_PASSWORD, generate_test_key

# Polytest Suite: DELETE v1_key

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
@pytest.mark.localnet
def test_basic_request_and_response_validation(
    localnet_kmd_client: KmdClient,
    wallet_handle: tuple[str, str, str],
) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    wallet_handle_token, _, _ = wallet_handle

    # Generate a key to delete
    address = generate_test_key(localnet_kmd_client, wallet_handle_token)

    # Verify key exists
    list_before = localnet_kmd_client.list_keys_in_wallet(
        ListKeysRequest(wallet_handle_token=wallet_handle_token)
    )
    assert address in (list_before.addresses or [])

    # Delete the key (returns empty response)
    localnet_kmd_client.delete_key(
        DeleteKeyRequest(
            address=address,
            wallet_handle_token=wallet_handle_token,
            wallet_password=TEST_WALLET_PASSWORD,
        )
    )

    # Verify key was deleted
    list_after = localnet_kmd_client.list_keys_in_wallet(
        ListKeysRequest(wallet_handle_token=wallet_handle_token)
    )
    assert address not in (list_after.addresses or [])
