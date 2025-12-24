import secrets

import pytest
from nacl.signing import SigningKey

from algokit_kmd_client import KmdClient
from algokit_kmd_client.models import ImportKeyRequest

from .fixtures import public_key_to_address

# Polytest Suite: POST v1_key_import

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
@pytest.mark.localnet
def test_basic_request_and_response_validation(
    localnet_kmd_client: KmdClient,
    wallet_handle: tuple[str, str, str],
) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    wallet_handle_token, _, _ = wallet_handle

    # Generate a random ed25519 keypair
    seed = secrets.token_bytes(32)
    signing_key = SigningKey(seed)
    # The private key for import is the 64-byte concatenation of seed + public key
    private_key = bytes(signing_key) + bytes(signing_key.verify_key)

    result = localnet_kmd_client.import_key(
        ImportKeyRequest(
            wallet_handle_token=wallet_handle_token,
            private_key=private_key,
        )
    )

    assert result.address is not None

    # Verify the imported key's address matches the public key
    expected_address = public_key_to_address(bytes(signing_key.verify_key))
    assert result.address == expected_address
