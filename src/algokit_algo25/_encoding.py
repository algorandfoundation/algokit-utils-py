"""11-bit encoding utilities for mnemonic conversion."""

from typing import Final

BITS_PER_WORD: Final[int] = 11
BITS_PER_BYTE: Final[int] = 8


def bytes_to_11bit_indices(data: bytes) -> list[int]:
    """Convert bytes to list of 11-bit indices.

    32 bytes (256 bits) -> 24 x 11-bit values (264 bits, 8 padding zeros).
    """
    buffer = 0
    num_bits = 0
    indices: list[int] = []
    for byte in data:
        buffer |= byte << num_bits
        num_bits += BITS_PER_BYTE
        while num_bits >= BITS_PER_WORD:
            indices.append(buffer & 0x7FF)
            buffer >>= BITS_PER_WORD
            num_bits -= BITS_PER_WORD
    if num_bits > 0:
        indices.append(buffer & 0x7FF)
    return indices


def indices_11bit_to_bytes(indices: list[int]) -> bytes:
    """Convert 11-bit indices to bytes.

    24 x 11-bit values (264 bits) -> 33 bytes (last byte is padding).
    """
    buffer = 0
    num_bits = 0
    output: list[int] = []
    for idx in indices:
        buffer |= idx << num_bits
        num_bits += BITS_PER_WORD
        while num_bits >= BITS_PER_BYTE:
            output.append(buffer & 0xFF)
            buffer >>= BITS_PER_BYTE
            num_bits -= BITS_PER_BYTE
    if num_bits > 0:
        output.append(buffer & 0xFF)
    return bytes(output)
