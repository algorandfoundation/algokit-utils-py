import base64

# Derived from py-algorand-sdk/algosdk/encoding.py (MIT License).

from Cryptodome.Hash import SHA512

from . import constants, error

__all__ = [
    "checksum",
    "decode_address",
    "encode_address",
    "is_valid_address",
]


def is_valid_address(addr: str | bytes | None) -> bool:
    """
    Check if the string address is a valid Algorand address.

    Args:
        addr: base32 address
    """
    if not isinstance(addr, str):
        return False

    if len(_undo_padding(addr)) != constants.address_len:
        return False

    try:
        decoded = decode_address(addr)
        return isinstance(decoded, bytes)
    except Exception:
        return False


def decode_address(addr: str | None) -> bytes | str | None:
    """
    Decode a string address into its address bytes and checksum.
    """
    if not addr:
        return addr
    if len(addr) != constants.address_len:
        raise error.WrongKeyLengthError

    decoded = base64.b32decode(_correct_padding(addr))
    addr_bytes = decoded[: -constants.check_sum_len_bytes]
    expected_checksum = decoded[-constants.check_sum_len_bytes :]
    chksum = _checksum(addr_bytes)

    if chksum == expected_checksum:
        return addr_bytes
    raise error.WrongChecksumError


def encode_address(addr_bytes: bytes | None) -> bytes | str | None:
    """
    Encode a byte address into a string composed of the encoded bytes and the checksum.
    """
    if not addr_bytes:
        return addr_bytes
    if len(addr_bytes) != constants.key_len_bytes:
        raise error.WrongKeyBytesLengthError
    chksum = _checksum(addr_bytes)
    addr = base64.b32encode(addr_bytes + chksum)
    return _undo_padding(addr.decode())


def checksum(data: bytes) -> bytes:
    """
    Compute the checksum of arbitrary binary input.
    """
    digest = SHA512.new(truncate="256")
    digest.update(data)
    return digest.digest()


def _checksum(addr_bytes: bytes) -> bytes:
    return checksum(addr_bytes)[-constants.check_sum_len_bytes :]


def _correct_padding(value: str) -> str:
    if len(value) % 8 == 0:
        return value
    return value + "=" * (8 - len(value) % 8)


def _undo_padding(value: str) -> str:
    return value.strip("=")
