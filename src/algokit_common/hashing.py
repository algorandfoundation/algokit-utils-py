from typing import Final

from Cryptodome.Hash import SHA512


def sha512_256(data: bytes) -> bytes:
    ch = SHA512.new(truncate="256")
    ch.update(data)
    return ch.digest()


BASE32_ALPHABET_NO_PAD: Final[bytes] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"


def base32_nopad_encode(data: bytes) -> str:
    import base64

    return base64.b32encode(data).decode().rstrip("=")


def base32_nopad_decode(text: str) -> bytes:
    import base64

    pad_len = (-len(text)) % 8
    return base64.b32decode(text + ("=" * pad_len))
