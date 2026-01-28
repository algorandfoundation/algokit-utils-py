"""
Shared utilities for AlgoKit examples.

This module provides common utilities for LocalNet configuration,
console output, formatting, client creation, and account management.
"""

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
from .utils import (
    cleanup_test_wallet,
    create_algod_client,
    create_algorand_client,
    create_indexer_client,
    create_kmd_client,
    create_random_account,
    create_test_wallet,
    format_algo,
    format_bytes,
    format_hex,
    format_micro_algo,
    get_account_balance,
    get_funded_account,
    load_teal_source,
    print_error,
    print_header,
    print_info,
    print_step,
    print_success,
    shorten_address,
    wait_for_confirmation,
)

__all__ = [
    # Constants
    "ALGOD_PORT",
    "ALGOD_SERVER",
    "ALGOD_TOKEN",
    "INDEXER_PORT",
    "INDEXER_SERVER",
    "INDEXER_TOKEN",
    "KMD_PORT",
    "KMD_SERVER",
    "KMD_TOKEN",
    "cleanup_test_wallet",
    # Client creation helpers
    "create_algod_client",
    "create_algorand_client",
    "create_indexer_client",
    "create_kmd_client",
    "create_random_account",
    # KMD helpers
    "create_test_wallet",
    # Formatting helpers
    "format_algo",
    "format_bytes",
    "format_hex",
    "format_micro_algo",
    "get_account_balance",
    # Account helpers
    "get_funded_account",
    # TEAL artifact helpers
    "load_teal_source",
    "print_error",
    # Console output helpers
    "print_header",
    "print_info",
    "print_step",
    "print_success",
    "shorten_address",
    # Transaction helpers
    "wait_for_confirmation",
]
