"""
Shared utility functions for examples.

This module provides helper functions for console output, formatting,
client creation, wallet management, transactions, and accounts.
"""

from __future__ import annotations

import contextlib
import secrets
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from algokit_algod_client import AlgodClient
from algokit_algod_client.config import ClientConfig as AlgodConfig
from algokit_indexer_client import IndexerClient
from algokit_indexer_client.config import ClientConfig as IndexerConfig
from algokit_kmd_client import KmdClient
from algokit_kmd_client.config import ClientConfig as KmdConfig
from algokit_kmd_client.models import (
    CreateWalletRequest,
    InitWalletHandleTokenRequest,
    ReleaseWalletHandleTokenRequest,
)
from algokit_utils import AlgoAmount, AlgorandClient

from .constants import (
    ALGOD_PORT,
    ALGOD_SERVER,
    ALGOD_TOKEN,
    INDEXER_PORT,
    INDEXER_SERVER,
    INDEXER_TOKEN,
    KMD_PORT,
    KMD_SERVER,
    KMD_TOKEN,
)

if TYPE_CHECKING:
    from algokit_utils.accounts.account_manager import AddressAndSigner


# ============================================================================
# Console Output Helpers
# ============================================================================


def print_header(title: str) -> None:
    """Print a header for an example section."""
    line = "=" * 60
    print(f"\n{line}")  # noqa: T201
    print(f"  {title}")  # noqa: T201
    print(f"{line}\n")  # noqa: T201


def print_step(step: int, description: str) -> None:
    """Print a step in the example."""
    print(f"\n  Step {step}: {description}")  # noqa: T201


def print_info(message: str) -> None:
    """Print informational message."""
    print(f"    {message}")  # noqa: T201


def print_success(message: str) -> None:
    """Print success message."""
    print(f"    [OK] {message}")  # noqa: T201


def print_error(message: str) -> None:
    """Print error message."""
    print(f"    [ERROR] {message}")  # noqa: T201


# ============================================================================
# Formatting Helpers
# ============================================================================


def format_algo(amount: AlgoAmount | int | Decimal, decimals: int = 6) -> str:
    """
    Format an AlgoAmount or microAlgo value to a human-readable string.

    Args:
        amount: An AlgoAmount object or microAlgo value (int or Decimal)
        decimals: Number of decimal places to show

    Returns:
        Formatted string like "1.000000 ALGO"
    """
    if isinstance(amount, AlgoAmount):
        algo_value = amount.algo
    else:
        # Assume microAlgo value
        algo_value = Decimal(amount) / Decimal(1_000_000)

    return f"{algo_value:.{decimals}f} ALGO"


def format_micro_algo(micro_algo: int) -> str:
    """
    Format a microAlgo amount to a human-readable string.

    Args:
        micro_algo: Amount in microAlgos

    Returns:
        Formatted string like "1,000,000 microALGO"
    """
    return f"{micro_algo:,} microALGO"


def shorten_address(address: str, prefix_length: int = 6, suffix_length: int = 4) -> str:
    """
    Shorten an Algorand address for display.

    Args:
        address: Full Algorand address
        prefix_length: Number of characters to show at the start
        suffix_length: Number of characters to show at the end

    Returns:
        Shortened address like "ABC123...WXYZ"
    """
    if len(address) <= prefix_length + suffix_length + 3:
        return address
    return f"{address[:prefix_length]}...{address[-suffix_length:]}"


def format_bytes(data: bytes, max_preview_bytes: int = 8) -> str:
    """
    Format a byte array as a readable string showing length and preview.

    Args:
        data: Bytes to format
        max_preview_bytes: Maximum number of bytes to show in preview

    Returns:
        Formatted string like "32 bytes: [0x01, 0x02, ...]"
    """
    preview = ", ".join(f"0x{b:02x}" for b in data[:max_preview_bytes])
    suffix = ", ..." if len(data) > max_preview_bytes else ""
    return f"{len(data)} bytes: [{preview}{suffix}]"


def format_hex(data: bytes) -> str:
    """
    Format a byte array as a hexadecimal string.

    Args:
        data: Bytes to format

    Returns:
        Hex string like "0x0102030405"
    """
    return f"0x{data.hex()}"


# ============================================================================
# Client Creation Helpers
# ============================================================================


def create_algod_client() -> AlgodClient:
    """Create an Algod client using default LocalNet configuration."""
    config = AlgodConfig(
        base_url=f"{ALGOD_SERVER}:{ALGOD_PORT}",
        token=ALGOD_TOKEN,
    )
    return AlgodClient(config)


def create_kmd_client() -> KmdClient:
    """Create a KMD client using default LocalNet configuration."""
    config = KmdConfig(
        base_url=f"{KMD_SERVER}:{KMD_PORT}",
        token=KMD_TOKEN,
    )
    return KmdClient(config)


def create_indexer_client() -> IndexerClient:
    """Create an Indexer client using default LocalNet configuration."""
    config = IndexerConfig(
        base_url=f"{INDEXER_SERVER}:{INDEXER_PORT}",
        token=INDEXER_TOKEN,
    )
    return IndexerClient(config)


def create_algorand_client() -> AlgorandClient:
    """Create an AlgorandClient configured for LocalNet."""
    return AlgorandClient.default_localnet()


# ============================================================================
# KMD Helpers
# ============================================================================


def _generate_wallet_name() -> str:
    """Generate a unique wallet name for testing."""
    random_suffix = secrets.token_hex(4)
    return f"test-wallet-{random_suffix}"


def create_test_wallet(
    kmd: KmdClient,
    password: str = "",
) -> dict[str, str]:
    """
    Create a test wallet for examples.

    Args:
        kmd: KMD client instance
        password: Wallet password (default: empty string)

    Returns:
        Dictionary with wallet_id, wallet_name, and wallet_handle_token
    """
    wallet_name = _generate_wallet_name()

    # Create the wallet
    create_result = kmd.create_wallet(
        CreateWalletRequest(wallet_name=wallet_name, wallet_password=password, wallet_driver_name="sqlite")
    )
    wallet_id = create_result.wallet.id_

    # Initialize the wallet handle (unlock the wallet)
    init_result = kmd.init_wallet_handle(InitWalletHandleTokenRequest(wallet_id=wallet_id, wallet_password=password))
    wallet_handle_token = init_result.wallet_handle_token

    return {
        "wallet_id": wallet_id,
        "wallet_name": wallet_name,
        "wallet_handle_token": wallet_handle_token,
    }


def cleanup_test_wallet(kmd: KmdClient, wallet_handle_token: str) -> None:
    """
    Cleanup a test wallet by releasing its handle token.

    Note: KMD doesn't support deleting wallets, so we just release the handle.

    Args:
        kmd: KMD client instance
        wallet_handle_token: The wallet handle token to release
    """
    # Ignore errors during cleanup (handle may have already expired)
    with contextlib.suppress(Exception):
        kmd.release_wallet_handle_token(ReleaseWalletHandleTokenRequest(wallet_handle_token=wallet_handle_token))


# ============================================================================
# Transaction Helpers
# ============================================================================


def wait_for_confirmation(
    algod: AlgodClient,
    tx_id: str,
    max_rounds: int = 5,
) -> object:
    """
    Wait for a transaction to be confirmed.

    Args:
        algod: Algod client instance
        tx_id: Transaction ID to wait for
        max_rounds: Maximum number of rounds to wait

    Returns:
        The pending transaction response once confirmed

    Raises:
        Exception: If transaction is rejected or not confirmed within max_rounds
    """
    status = algod.status()
    current_round = status.last_round
    end_round = current_round + max_rounds

    while current_round < end_round:
        pending_info = algod.pending_transaction_information(tx_id)

        if pending_info.confirmed_round is not None and pending_info.confirmed_round > 0:
            return pending_info

        pool_error = pending_info.pool_error
        if pool_error:
            raise Exception(f"Transaction rejected: {pool_error}")

        algod.status_after_block(current_round)
        current_round += 1

    raise Exception(f"Transaction {tx_id} not confirmed after {max_rounds} rounds")


def get_account_balance(algorand: AlgorandClient, address: str) -> AlgoAmount:
    """
    Get the balance of an account.

    Args:
        algorand: AlgorandClient instance
        address: Account address to check

    Returns:
        Account balance as AlgoAmount
    """
    info = algorand.account.get_information(address)
    return info.amount


# ============================================================================
# Account Helpers
# ============================================================================


def get_funded_account(algorand: AlgorandClient) -> AddressAndSigner:
    """
    Get a funded account from the LocalNet dispenser.

    Args:
        algorand: AlgorandClient instance

    Returns:
        The dispenser account with signing capabilities
    """
    return algorand.account.localnet_dispenser()


def create_random_account(
    algorand: AlgorandClient,
    funding_amount: AlgoAmount | None = None,
) -> AddressAndSigner:
    """
    Create a random account and fund it from the dispenser.

    Args:
        algorand: AlgorandClient instance
        funding_amount: Amount to fund (default: 10 ALGO)

    Returns:
        The funded random account with signing capabilities
    """
    account = algorand.account.random()
    dispenser = algorand.account.localnet_dispenser()

    amount = funding_amount if funding_amount is not None else AlgoAmount.from_algo(10)

    algorand.account.ensure_funded(
        account_to_fund=account.addr,
        dispenser_account=dispenser,
        min_spending_balance=amount,
    )

    algorand.set_signer(sender=account.addr, signer=account.signer)

    return account


# ============================================================================
# TEAL Artifact Helpers
# ============================================================================

# Path to the artifacts directory
_ARTIFACTS_DIR = Path(__file__).parent / "artifacts"


def load_teal_source(filename: str) -> str:
    """
    Load a TEAL source file from the shared artifacts directory.

    Args:
        filename: Name of the TEAL file (e.g., "approval-counter.teal")

    Returns:
        The TEAL source code as a string

    Raises:
        FileNotFoundError: If the specified file does not exist
    """
    file_path = _ARTIFACTS_DIR / filename
    return file_path.read_text()
