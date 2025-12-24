import base64

import pytest

from algokit_algod_client import AlgodClient
from algokit_kmd_client import KmdClient
from algokit_kmd_client.models import SignProgramRequest

from .fixtures import TEST_WALLET_PASSWORD, generate_test_key

# Polytest Suite: POST v1_program_sign

# Polytest Group: Common Tests


@pytest.mark.group_common_tests
@pytest.mark.localnet
def test_basic_request_and_response_validation(
    localnet_kmd_client: KmdClient,
    localnet_algod_client: AlgodClient,
    wallet_handle: tuple[str, str, str],
) -> None:
    """Given a known request validate that the same request can be made using our models. Then, validate that our response model aligns with the known response"""
    wallet_handle_token, _, _ = wallet_handle

    # Generate a key
    address = generate_test_key(localnet_kmd_client, wallet_handle_token)

    # Compile a simple TEAL program (always approves)
    teal_source = b"#pragma version 8\nint 1"
    compile_result = localnet_algod_client.teal_compile(teal_source)
    program_bytes = base64.b64decode(compile_result.result)

    # Sign the program
    result = localnet_kmd_client.sign_program(
        SignProgramRequest(
            wallet_handle_token=wallet_handle_token,
            address=address,
            program=program_bytes,
            wallet_password=TEST_WALLET_PASSWORD,
        )
    )

    assert result.sig is not None
