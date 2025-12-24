import pytest

from algokit_kmd_client import KmdClient
from algokit_kmd_client.models import ExportMultisigRequest

from .fixtures import create_test_multisig

# Polytest Suite: POST v1_multisig_export

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
    multisig_address, public_keys, _, threshold = create_test_multisig(localnet_kmd_client, wallet_handle_token)

    result = localnet_kmd_client.export_multisig(
        ExportMultisigRequest(
            wallet_handle_token=wallet_handle_token,
            address=multisig_address,
        )
    )

    assert result.multisig_version == 1
    assert result.threshold == threshold
    assert result.public_keys == public_keys
