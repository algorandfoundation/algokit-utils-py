from __future__ import annotations

import hashlib
from typing import Final


def sha512_256(data: bytes) -> bytes:
    """Return SHA-512/256 digest of data.

    Uses hashlib if available, otherwise tries Cryptodome fallback.
    """
    try:
        h = hashlib.new("sha512_256")
    except ValueError:  # pragma: no cover - fallback path
        try:
            from Cryptodome.Hash import SHA512 as _SHA512  # type: ignore

            ch = _SHA512.new(truncate="256")
            ch.update(data)
            return ch.digest()
        except Exception as exc:  # pragma: no cover - explicit failure
            raise RuntimeError("sha512_256 not available; install pycryptodome") from exc
    h.update(data)
    return h.digest()


BASE32_ALPHABET_NO_PAD: Final[bytes] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"


def base32_nopad_encode(data: bytes) -> str:
    import base64

    return base64.b32encode(data).decode().rstrip("=")


def base32_nopad_decode(text: str) -> bytes:
    import base64

    pad_len = (-len(text)) % 8
    return base64.b32decode(text + ("=" * pad_len))
