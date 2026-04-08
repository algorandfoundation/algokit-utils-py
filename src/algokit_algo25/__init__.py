"""Algorand 25-word mnemonic encoding/decoding (algokit-algo25)."""

from algokit_algo25.exceptions import (
    FAIL_TO_DECODE_MNEMONIC_ERROR_MSG,
    NOT_IN_WORDS_LIST_ERROR_MSG,
    InvalidMnemonicError,
    InvalidSeedLengthError,
    MnemonicError,
    WordNotFoundError,
)
from algokit_algo25.mnemonic import (
    KEY_LEN_BYTES,
    MNEMONIC_LEN,
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
