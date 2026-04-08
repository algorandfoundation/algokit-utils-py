"""Algorand 25-word mnemonic utilities.

Re-exports from algokit_algo25 for convenient access via algokit_utils.algo25.

Usage:
    from algokit_utils import algo25
    mnemonic = algo25.mnemonic_from_seed(seed)

    # Or import directly:
    from algokit_utils.algo25 import mnemonic_from_seed, seed_from_mnemonic
"""

from algokit_algo25 import (
    FAIL_TO_DECODE_MNEMONIC_ERROR_MSG,
    KEY_LEN_BYTES,
    MNEMONIC_LEN,
    NOT_IN_WORDS_LIST_ERROR_MSG,
    InvalidMnemonicError,
    InvalidSeedLengthError,
    MnemonicError,
    WordNotFoundError,
    master_derivation_key_to_mnemonic,
    mnemonic_from_seed,
    mnemonic_to_master_derivation_key,
    secret_key_to_mnemonic,
    seed_from_mnemonic,
)

__all__ = [
    # Constants
    "FAIL_TO_DECODE_MNEMONIC_ERROR_MSG",
    "KEY_LEN_BYTES",
    "MNEMONIC_LEN",
    "NOT_IN_WORDS_LIST_ERROR_MSG",
    # Exceptions
    "InvalidMnemonicError",
    "InvalidSeedLengthError",
    "MnemonicError",
    "WordNotFoundError",
    # Functions
    "master_derivation_key_to_mnemonic",
    "mnemonic_from_seed",
    "mnemonic_to_master_derivation_key",
    "secret_key_to_mnemonic",
    "seed_from_mnemonic",
]
