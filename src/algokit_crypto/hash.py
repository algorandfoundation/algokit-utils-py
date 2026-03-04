"""Algorand-compatible hashing utilities."""

from algokit_common.constants import HASH_BYTES_LENGTH
from algokit_common.hashing import sha512_256


def hash(data: bytes) -> bytes:
    """Compute an Algorand-compatible SHA-512/256 hash.

    Args:
        data: The bytes to hash.

    Returns:
        The first HASH_BYTES_LENGTH bytes of the SHA-512/256 digest.
    """
    return sha512_256(data)[:HASH_BYTES_LENGTH]
