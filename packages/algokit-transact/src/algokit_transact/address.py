from __future__ import annotations

from .constants import CHECKSUM_BYTE_LENGTH, PUBLIC_KEY_BYTE_LENGTH
from .hashing import base32_nopad_decode, base32_nopad_encode, sha512_256


def public_key_from_address(address: str) -> bytes:
    if not isinstance(address, str):
        raise TypeError("address must be str")
    raw = base32_nopad_decode(address)
    if len(raw) != PUBLIC_KEY_BYTE_LENGTH + CHECKSUM_BYTE_LENGTH:
        raise ValueError("invalid address length")
    pk = raw[:PUBLIC_KEY_BYTE_LENGTH]
    checksum = raw[PUBLIC_KEY_BYTE_LENGTH:]
    expected = sha512_256(pk)[-CHECKSUM_BYTE_LENGTH:]
    if checksum != expected:
        raise ValueError("invalid address checksum")
    return pk


def address_from_public_key(public_key: bytes) -> str:
    if len(public_key) != PUBLIC_KEY_BYTE_LENGTH:
        raise ValueError("invalid public key length")
    checksum = sha512_256(public_key)[-CHECKSUM_BYTE_LENGTH:]
    return base32_nopad_encode(public_key + checksum)
