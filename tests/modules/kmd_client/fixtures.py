"""Helper fixtures and utilities for KMD client localnet tests.

These fixtures mirror the TypeScript test fixtures for polytest compatibility.
"""

from uuid import uuid4

from algokit_common import address_from_public_key, public_key_from_address

from algokit_kmd_client import KmdClient
from algokit_kmd_client.models import (
    CreateWalletRequest,
    GenerateKeyRequest,
    ImportMultisigRequest,
    InitWalletHandleTokenRequest,
    ReleaseWalletHandleTokenRequest,
)

# Test constants matching TypeScript tests
TEST_WALLET_PASSWORD = "test-password-123"
TEST_WALLET_DRIVER = "sqlite"
MULTISIG_VERSION = 1
MULTISIG_THRESHOLD = 2
MULTISIG_KEY_COUNT = 3


def generate_wallet_name() -> str:
    """Generates a unique wallet name for testing."""
    return f"test-wallet-{uuid4().hex[:12]}"


def create_test_wallet(
    client: KmdClient,
    password: str = TEST_WALLET_PASSWORD,
) -> tuple[str, str]:
    """Creates a test wallet and returns (wallet_id, wallet_name)."""
    wallet_name = generate_wallet_name()
    result = client.create_wallet(
        CreateWalletRequest(
            wallet_name=wallet_name,
            wallet_password=password,
            wallet_driver_name=TEST_WALLET_DRIVER,
        )
    )
    assert result.wallet is not None
    assert result.wallet.id_ is not None
    return result.wallet.id_, result.wallet.name or wallet_name


def get_wallet_handle(
    client: KmdClient,
    password: str = TEST_WALLET_PASSWORD,
) -> tuple[str, str, str]:
    """Creates a wallet and initializes a wallet handle token.

    Returns (wallet_handle_token, wallet_id, wallet_name).
    """
    wallet_id, wallet_name = create_test_wallet(client, password)

    init_result = client.init_wallet_handle(
        InitWalletHandleTokenRequest(
            wallet_id=wallet_id,
            wallet_password=password,
        )
    )
    assert init_result.wallet_handle_token is not None

    return init_result.wallet_handle_token, wallet_id, wallet_name


def release_wallet_handle(client: KmdClient, wallet_handle_token: str) -> None:
    """Releases a wallet handle token (locks wallet). Used for cleanup in tests."""
    try:
        client.release_wallet_handle_token(ReleaseWalletHandleTokenRequest(wallet_handle_token=wallet_handle_token))
    except Exception as e:
        print(f"Failed to release wallet handle: {e}")  # noqa: T201
        # Ignore errors during cleanup (handle may have already expired)


def generate_test_key(client: KmdClient, wallet_handle_token: str) -> str:
    """Generates a key in the wallet and returns the address string."""
    result = client.generate_key(GenerateKeyRequest(wallet_handle_token=wallet_handle_token))
    assert result.address is not None
    return result.address


def generate_multiple_keys(
    client: KmdClient,
    wallet_handle_token: str,
    count: int = MULTISIG_KEY_COUNT,
) -> list[str]:
    """Generates multiple keys for multisig tests."""
    addresses: list[str] = []
    for _ in range(count):
        address = generate_test_key(client, wallet_handle_token)
        addresses.append(address)
    return addresses


def address_to_public_key(address: str) -> bytes:
    """Converts an Algorand address string to a public key bytes."""
    return public_key_from_address(address)


def public_key_to_address(public_key: bytes) -> str:
    """Converts a public key to an Algorand address string."""
    return address_from_public_key(public_key)


def create_test_multisig(
    client: KmdClient,
    wallet_handle_token: str,
    threshold: int = MULTISIG_THRESHOLD,
    key_count: int = MULTISIG_KEY_COUNT,
) -> tuple[str, list[bytes], list[str], int]:
    """Creates a multisig account with test keys.

    Returns (multisig_address, public_keys, addresses, threshold).
    """
    # Generate keys
    addresses = generate_multiple_keys(client, wallet_handle_token, key_count)
    public_keys = [address_to_public_key(addr) for addr in addresses]

    # Import multisig
    result = client.import_multisig(
        ImportMultisigRequest(
            wallet_handle_token=wallet_handle_token,
            multisig_version=MULTISIG_VERSION,
            threshold=threshold,
            public_keys=public_keys,
        )
    )
    assert result.address is not None

    return result.address, public_keys, addresses, threshold
