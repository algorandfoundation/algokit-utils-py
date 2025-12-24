import pytest

from algokit_kmd_client import KmdClient
from algokit_kmd_client.models import DeleteMultisigRequest, ListMultisigRequest

from .fixtures import TEST_WALLET_PASSWORD, create_test_multisig

# Polytest Suite: DELETE v1_multisig

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
@pytest.mark.localnet
def test_basic_request_and_response_validation(
    localnet_kmd_client: KmdClient,
    wallet_handle: tuple[str, str, str],
) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    wallet_handle_token, _, _ = wallet_handle

    # Create a multisig first
    multisig_address, _, _, _ = create_test_multisig(localnet_kmd_client, wallet_handle_token)

    # Verify multisig exists
    list_before = localnet_kmd_client.list_multisig(
        ListMultisigRequest(wallet_handle_token=wallet_handle_token)
    )
    assert multisig_address in (list_before.addresses or [])

    # Delete the multisig (returns empty response)
    localnet_kmd_client.delete_multisig(
        DeleteMultisigRequest(
            address=multisig_address,
            wallet_handle_token=wallet_handle_token,
            wallet_password=TEST_WALLET_PASSWORD,
        )
    )

    # Verify multisig was deleted
    list_after = localnet_kmd_client.list_multisig(
        ListMultisigRequest(wallet_handle_token=wallet_handle_token)
    )
    assert multisig_address not in (list_after.addresses or [])
