import base64

from nacl.signing import SigningKey

# Vendored from py-algorand-sdk/algosdk/logic.py (MIT License).

from . import constants, encoding
from .error import InvalidProgram

__all__ = [
    "address",
    "get_application_address",
    "teal_sign",
    "teal_sign_from_program",
]


def address(program: bytes) -> str:
    """Return the address of the program."""
    to_sign = constants.logic_prefix + program
    checksum = encoding.checksum(to_sign)
    encoded = encoding.encode_address(checksum)
    assert isinstance(encoded, str)
    return encoded


def teal_sign(private_key: str, data: bytes, contract_addr: str) -> bytes:
    """
    Return the signature suitable for ed25519verify TEAL opcode.
    """
    decoded_key = base64.b64decode(private_key)
    signing_key = SigningKey(decoded_key[: constants.key_len_bytes])

    contract_bytes = encoding.decode_address(contract_addr)
    if not isinstance(contract_bytes, bytes):
        raise InvalidProgram("contract address failed to decode")

    to_sign = constants.logic_data_prefix + contract_bytes + data
    signed = signing_key.sign(to_sign)
    return signed.signature


def teal_sign_from_program(private_key: str, data: bytes, program: bytes) -> bytes:
    """
    Return the signature suitable for ed25519verify TEAL opcode using the program hash.
    """
    return teal_sign(private_key, data, address(program))


def get_application_address(app_id: int) -> str:
    """
    Return the escrow address of an application.
    """
    if not isinstance(app_id, int):
        raise TypeError(f"Expected an int for app_id but received {type(app_id)}")

    to_sign = constants.APPID_PREFIX + app_id.to_bytes(8, "big")
    checksum = encoding.checksum(to_sign)
    encoded = encoding.encode_address(checksum)
    assert isinstance(encoded, str)
    return encoded
