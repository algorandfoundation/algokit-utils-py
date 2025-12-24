import pytest

from algokit_kmd_client import KmdClient
from algokit_kmd_client.models import ListMultisigRequest

from .fixtures import create_test_multisig

# Polytest Suite: POST v1_multisig_list

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

    result = localnet_kmd_client.list_multisig(
        ListMultisigRequest(wallet_handle_token=wallet_handle_token)
    )

    assert result.addresses is not None
    # Verify the multisig is in the list
    assert multisig_address in result.addresses
