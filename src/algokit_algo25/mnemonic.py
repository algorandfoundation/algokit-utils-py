"""Algorand mnemonic encoding/decoding (25-word BIP39 format)."""

from typing import Final

from algokit_algo25._encoding import bytes_to_11bit_indices, indices_11bit_to_bytes
from algokit_algo25._wordlist import INDEX_TO_WORD, WORD_TO_INDEX
from algokit_algo25.exceptions import (
    FAIL_TO_DECODE_MNEMONIC_ERROR_MSG,
    NOT_IN_WORDS_LIST_ERROR_MSG,
    InvalidMnemonicError,
    InvalidSeedLengthError,
    WordNotFoundError,
)
from algokit_common import sha512_256

KEY_LEN_BYTES: Final[int] = 32
MNEMONIC_LEN: Final[int] = 25


def _compute_checksum_index(seed: bytes) -> int:
    """Compute checksum word index: first 11 bits of SHA512/256(seed)."""
    hash_bytes = sha512_256(seed)
    return bytes_to_11bit_indices(hash_bytes[:2])[0]


def mnemonic_from_seed(seed: bytes) -> str:
    """Convert 32-byte seed to 25-word mnemonic.

    Args:
        seed: 32-byte seed/key

    Returns:
        25-word mnemonic string (space-separated)

    Raises:
        InvalidSeedLengthError: If seed is not 32 bytes
    """
    if len(seed) != KEY_LEN_BYTES:
        raise InvalidSeedLengthError(f"seed must be {KEY_LEN_BYTES} bytes, got {len(seed)}")

    indices = bytes_to_11bit_indices(seed)
    words = [INDEX_TO_WORD[i] for i in indices]
    checksum_idx = _compute_checksum_index(seed)
    words.append(INDEX_TO_WORD[checksum_idx])
    return " ".join(words)


def seed_from_mnemonic(mnemonic: str) -> bytes:
    """Convert 25-word mnemonic to 32-byte seed.

    Args:
        mnemonic: 25-word mnemonic string (space-separated)

    Returns:
        32-byte seed

    Raises:
        InvalidMnemonicError: If word count, checksum, or padding invalid
        WordNotFoundError: If word not in wordlist
    """
    words = mnemonic.lower().split()
    if len(words) != MNEMONIC_LEN:
        raise InvalidMnemonicError(
            f"{FAIL_TO_DECODE_MNEMONIC_ERROR_MSG}: expected {MNEMONIC_LEN} words, got {len(words)}"
        )

    try:
        indices = [WORD_TO_INDEX[w] for w in words[:-1]]
        checksum_idx = WORD_TO_INDEX[words[-1]]
    except KeyError as e:
        raise WordNotFoundError(f"{NOT_IN_WORDS_LIST_ERROR_MSG}: {e.args[0]}") from e

    data = indices_11bit_to_bytes(indices)

    # Verify padding (last byte must be 0)
    if data[-1] != 0:
        raise InvalidMnemonicError(f"{FAIL_TO_DECODE_MNEMONIC_ERROR_MSG}: invalid padding")

    seed = data[:KEY_LEN_BYTES]

    # Verify checksum
    expected_checksum = _compute_checksum_index(seed)
    if checksum_idx != expected_checksum:
        raise InvalidMnemonicError(f"{FAIL_TO_DECODE_MNEMONIC_ERROR_MSG}: checksum mismatch")

    return seed


def secret_key_to_mnemonic(secret_key: bytes) -> str:
    """Convert 64-byte secret key to mnemonic.

    The first 32 bytes of an Algorand secret key are the seed.

    Args:
        secret_key: 64-byte secret key (seed || public_key)

    Returns:
        25-word mnemonic
    """
    return mnemonic_from_seed(secret_key[:KEY_LEN_BYTES])


def mnemonic_to_master_derivation_key(mnemonic: str) -> bytes:
    """Convert mnemonic to master derivation key.

    Alias for seed_from_mnemonic (MDK = seed).

    Args:
        mnemonic: 25-word mnemonic string

    Returns:
        32-byte master derivation key
    """
    return seed_from_mnemonic(mnemonic)


def master_derivation_key_to_mnemonic(key: bytes) -> str:
    """Convert master derivation key to mnemonic.

    Alias for mnemonic_from_seed (MDK = seed).

    Args:
        key: 32-byte master derivation key

    Returns:
        25-word mnemonic string
    """
    return mnemonic_from_seed(key)
