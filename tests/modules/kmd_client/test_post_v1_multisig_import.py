import pytest

from algokit_kmd_client import KmdClient
from algokit_kmd_client.models import ImportMultisigRequest
from algokit_transact import address_from_multisig_signature, new_multisig_signature

from .fixtures import (
    MULTISIG_KEY_COUNT,
    MULTISIG_THRESHOLD,
    MULTISIG_VERSION,
    address_to_public_key,
    generate_multiple_keys,
)

# Polytest Suite: POST v1_multisig_import

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
@pytest.mark.localnet
def test_basic_request_and_response_validation(
    localnet_kmd_client: KmdClient,
    wallet_handle: tuple[str, str, str],
) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    wallet_handle_token, _, _ = wallet_handle

    # Generate keys for multisig
    addresses = generate_multiple_keys(localnet_kmd_client, wallet_handle_token, MULTISIG_KEY_COUNT)
    public_keys = [address_to_public_key(addr) for addr in addresses]

    # Calculate expected multisig address
    msig = new_multisig_signature(MULTISIG_VERSION, MULTISIG_THRESHOLD, addresses)
    expected_address = address_from_multisig_signature(msig)

    result = localnet_kmd_client.import_multisig(
        ImportMultisigRequest(
            wallet_handle_token=wallet_handle_token,
            multisig_version=MULTISIG_VERSION,
            threshold=MULTISIG_THRESHOLD,
            public_keys=public_keys,
        )
    )

    assert result.address == expected_address
