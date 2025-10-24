from __future__ import annotations

import pytest
from algokit_transact import decode_transaction


def test_malformed_bytes() -> None:
    with pytest.raises(ValueError, match="decoded msgpack is not a dict"):
        decode_transaction(b"\x01")


def test_encode_0_bytes() -> None:
    with pytest.raises(ValueError, match="^attempted to decode 0 bytes$"):
        decode_transaction(b"")
